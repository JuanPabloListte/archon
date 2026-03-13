"""CI/CD integration — audit check endpoint authenticated with API Key."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from app.database import get_session
from app.models.db import User, Project, AuditFinding
from app.api.deps import get_user_from_api_key

router = APIRouter()


class CheckOptions(BaseModel):
    threshold: int = 70         # fail if health_score < threshold
    fail_on: list[str] = ["critical"]  # severities that cause fail regardless of score


class CheckResult(BaseModel):
    status: str                 # "pass" | "fail"
    health_score: float
    total_findings: int
    critical_findings: int
    high_findings: int
    threshold: int
    fail_reasons: list[str]
    checked_at: str


@router.post("/{project_id}/audit/check", response_model=CheckResult)
def audit_check(
    project_id: str,
    options: CheckOptions = CheckOptions(),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_user_from_api_key),
):
    """
    Run a full audit synchronously and return pass/fail.
    Use from CI/CD with: -H "X-API-Key: ark_..."
    """
    project = session.exec(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Run audit synchronously
    from app.audit.engine import run_audit
    from app.reports.generator import generate_report

    findings = run_audit(project_id, session)
    report = generate_report(project_id, session)

    critical = sum(1 for f in findings if f.severity == "critical")
    high = sum(1 for f in findings if f.severity == "high")

    fail_reasons: list[str] = []
    if report.health_score < options.threshold:
        fail_reasons.append(f"Health score {report.health_score:.0f} is below threshold {options.threshold}")
    for sev in options.fail_on:
        count = sum(1 for f in findings if f.severity == sev)
        if count > 0:
            fail_reasons.append(f"{count} {sev} finding(s) detected")

    return CheckResult(
        status="fail" if fail_reasons else "pass",
        health_score=report.health_score,
        total_findings=len(findings),
        critical_findings=critical,
        high_findings=high,
        threshold=options.threshold,
        fail_reasons=fail_reasons,
        checked_at=datetime.utcnow().isoformat(),
    )
