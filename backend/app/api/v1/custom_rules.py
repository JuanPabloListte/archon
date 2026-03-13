"""Custom audit rules — CRUD and test endpoint."""
import yaml
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models.db import User, Project, CustomRule, ApiEndpoint, DbTable
from app.api.deps import get_current_user
from app.audit.custom_rule_engine import validate_rule_schema, evaluate_rule

router = APIRouter()

EXAMPLE_YAML = """\
name: "Example: DELETE endpoints without auth"
description: "All DELETE endpoints should require authentication"
category: security
severity: high
target: endpoints
conditions:
  - field: method
    operator: eq
    value: DELETE
  - field: auth_required
    operator: eq
    value: "false"
match: all
finding_title: "Unauthenticated DELETE endpoint: {path}"
finding_description: "The endpoint {method} {path} allows deletions without authentication."
finding_recommendation: "Add authentication middleware to protect this endpoint."
"""


class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_yaml: str


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_yaml: Optional[str] = None
    is_active: Optional[bool] = None


class RuleResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str]
    category: str
    severity: str
    target: str
    rule_yaml: str
    is_active: bool
    created_at: str
    updated_at: str


def _parse_yaml(rule_yaml: str) -> dict:
    try:
        return yaml.safe_load(rule_yaml) or {}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=422, detail=f"Invalid YAML: {e}")


def _to_response(r: CustomRule) -> RuleResponse:
    return RuleResponse(
        id=r.id, project_id=r.project_id, name=r.name,
        description=r.description, category=r.category,
        severity=r.severity, target=r.target, rule_yaml=r.rule_yaml,
        is_active=r.is_active, created_at=str(r.created_at), updated_at=str(r.updated_at),
    )


def _get_project_or_404(project_id: str, user: User, session: Session) -> Project:
    p = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("/{project_id}/rules", response_model=list[RuleResponse])
def list_rules(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    rules = session.exec(select(CustomRule).where(CustomRule.project_id == project_id)).all()
    return [_to_response(r) for r in rules]


@router.get("/{project_id}/rules/example")
def get_example(current_user: User = Depends(get_current_user)):
    return {"rule_yaml": EXAMPLE_YAML}


@router.post("/{project_id}/rules", response_model=RuleResponse, status_code=201)
def create_rule(project_id: str, body: RuleCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    rule_json = _parse_yaml(body.rule_yaml)
    errors = validate_rule_schema(rule_json)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})
    rule = CustomRule(
        project_id=project_id,
        name=body.name or rule_json.get("name", "Untitled"),
        description=body.description or rule_json.get("description"),
        category=rule_json.get("category", "security"),
        severity=rule_json.get("severity", "medium"),
        target=rule_json.get("target", "endpoints"),
        rule_yaml=body.rule_yaml,
        rule_json=rule_json,
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return _to_response(rule)


@router.patch("/{project_id}/rules/{rule_id}", response_model=RuleResponse)
def update_rule(project_id: str, rule_id: str, body: RuleUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    rule = session.exec(select(CustomRule).where(CustomRule.id == rule_id, CustomRule.project_id == project_id)).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if body.rule_yaml is not None:
        rule_json = _parse_yaml(body.rule_yaml)
        errors = validate_rule_schema(rule_json)
        if errors:
            raise HTTPException(status_code=422, detail={"validation_errors": errors})
        rule.rule_yaml = body.rule_yaml
        rule.rule_json = rule_json
        rule.category = rule_json.get("category", rule.category)
        rule.severity = rule_json.get("severity", rule.severity)
        rule.target = rule_json.get("target", rule.target)
    if body.name is not None:
        rule.name = body.name
    if body.description is not None:
        rule.description = body.description
    if body.is_active is not None:
        rule.is_active = body.is_active
    rule.updated_at = datetime.utcnow()
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return _to_response(rule)


@router.delete("/{project_id}/rules/{rule_id}", status_code=204)
def delete_rule(project_id: str, rule_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    rule = session.exec(select(CustomRule).where(CustomRule.id == rule_id, CustomRule.project_id == project_id)).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(rule)
    session.commit()


@router.post("/{project_id}/rules/{rule_id}/test")
def test_rule(project_id: str, rule_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Dry-run a rule against current project data — does NOT persist findings."""
    _get_project_or_404(project_id, current_user, session)
    rule = session.exec(select(CustomRule).where(CustomRule.id == rule_id, CustomRule.project_id == project_id)).first()
    if not rule or not rule.rule_json:
        raise HTTPException(status_code=404, detail="Rule not found or not parsed")
    endpoints = list(session.exec(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)).all())
    tables = list(session.exec(select(DbTable).where(DbTable.project_id == project_id)).all())
    findings = evaluate_rule(rule.rule_json, endpoints, tables, project_id)
    return {
        "matched": len(findings),
        "findings": [
            {"title": f.title, "severity": f.severity, "category": f.category,
             "description": f.description, "recommendation": f.recommendation}
            for f in findings
        ],
    }
