from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel
from app.database import get_session
from app.models.db import User, Project, AuditFinding
from app.api.deps import get_current_user

router = APIRouter()

class FindingResponse(BaseModel):
    id: str
    project_id: str
    severity: str
    category: str
    title: str
    description: str
    recommendation: str
    created_at: str

class AuditTriggerResponse(BaseModel):
    message: str
    project_id: str

@router.post("/run/{project_id}", response_model=AuditTriggerResponse)
def run_audit(
    project_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    background_tasks.add_task(run_audit_sync, project_id)
    return AuditTriggerResponse(message="Audit started", project_id=project_id)

def run_audit_sync(project_id: str):
    from app.workers.tasks import run_audit_task
    run_audit_task(project_id)

@router.get("/findings/{project_id}", response_model=List[FindingResponse])
def get_findings(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    findings = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()
    return [
        FindingResponse(
            id=f.id, project_id=f.project_id, severity=f.severity,
            category=f.category, title=f.title, description=f.description,
            recommendation=f.recommendation, created_at=str(f.created_at)
        ) for f in findings
    ]
