from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from typing import List, AsyncIterator
from pydantic import BaseModel
import json
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


@router.post("/run/{project_id}/stream")
async def run_audit_stream(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return StreamingResponse(
        _audit_stream(project_id, session),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _audit_stream(project_id: str, session: Session) -> AsyncIterator[str]:
    def sse(event: dict) -> str:
        return f"data: {json.dumps(event)}\n\n"

    try:
        from app.audit.rules.api import missing_auth, wrong_verb, duplicate_endpoint
        from app.audit.rules.database import missing_index, sensitive_column
        from app.audit.rules.security import sensitive_response
        from app.models.db import ApiEndpoint, DbTable
        from app.reports.generator import generate_report
        from app.rag.embeddings import index_project

        # Step 1: clear old findings
        yield sse({"type": "step", "text": "Clearing previous findings..."})
        old = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()
        for f in old:
            session.delete(f)
        session.commit()

        # Step 2: load data
        endpoints = list(session.exec(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)).all())
        tables = list(session.exec(select(DbTable).where(DbTable.project_id == project_id)).all())
        yield sse({"type": "step", "text": f"Loaded {len(endpoints)} endpoints and {len(tables)} tables"})

        all_findings: list[AuditFinding] = []

        # Step 3: API rules
        yield sse({"type": "step", "text": "Running API rules...", "group": True})
        for rule in [missing_auth, wrong_verb, duplicate_endpoint]:
            found = rule.check(endpoints, project_id)
            all_findings += found
            yield sse({"type": "rule", "rule": rule.__name__.split(".")[-1], "count": len(found)})

        # Step 4: Database rules
        yield sse({"type": "step", "text": "Running database rules...", "group": True})
        for rule in [missing_index, sensitive_column]:
            found = rule.check(tables, project_id)
            all_findings += found
            yield sse({"type": "rule", "rule": rule.__name__.split(".")[-1], "count": len(found)})

        # Step 5: Security rules
        yield sse({"type": "step", "text": "Running security rules...", "group": True})
        for rule in [sensitive_response]:
            found = rule.check(endpoints, project_id)
            all_findings += found
            yield sse({"type": "rule", "rule": rule.__name__.split(".")[-1], "count": len(found)})

        # Step 6: save
        yield sse({"type": "step", "text": f"Saving {len(all_findings)} findings..."})
        for f in all_findings:
            session.add(f)
        session.commit()

        # Step 7: report
        yield sse({"type": "step", "text": "Generating report..."})
        report = generate_report(project_id, session)

        # Step 8: RAG index
        yield sse({"type": "step", "text": "Indexing embeddings for RAG..."})
        try:
            index_project(project_id, session)
        except Exception:
            pass  # RAG indexing is optional, don't fail the audit

        yield sse({
            "type": "done",
            "total_findings": len(all_findings),
            "health_score": report.health_score,
            "summary": report.summary,
        })

    except Exception as e:
        yield sse({"type": "error", "text": str(e)})


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
