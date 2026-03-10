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

class InsightsResponse(BaseModel):
    prioritized: List[dict]
    summary: str

class AdviceResponse(BaseModel):
    finding_id: str
    recommendations: str

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


@router.get("/insights/{project_id}", response_model=InsightsResponse)
async def get_insights(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    from app.agents.auditor_agent import AuditorAgent
    result = await AuditorAgent(project_id, session).prioritize_findings()
    return InsightsResponse(**result)


@router.get("/findings/{finding_id}/advice", response_model=AdviceResponse)
async def get_finding_advice(
    finding_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    finding = session.exec(select(AuditFinding).where(AuditFinding.id == finding_id)).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    # Verify the finding belongs to a project owned by the current user
    project = session.exec(select(Project).where(Project.id == finding.project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Finding not found")
    from app.agents.advisor_agent import AdvisorAgent
    result = await AdvisorAgent(finding.project_id, session).get_recommendations(finding_id)
    return AdviceResponse(**result)
