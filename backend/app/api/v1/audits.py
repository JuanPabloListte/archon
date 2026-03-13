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
    source: str = "rule"
    status: str = "open"
    created_at: str

class AuditTriggerResponse(BaseModel):
    message: str
    project_id: str

class AuditRunOptions(BaseModel):
    system_prompt: str | None = None
    connection_ids: list[str] | None = None  # None = all connections

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
    body: AuditRunOptions = AuditRunOptions(),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    background_tasks.add_task(run_audit_sync, project_id, body.system_prompt, body.connection_ids)
    return AuditTriggerResponse(message="Audit started", project_id=project_id)

def run_audit_sync(project_id: str, system_prompt: str | None = None, connection_ids: list[str] | None = None):
    from app.workers.tasks import run_audit_task
    run_audit_task(project_id, system_prompt=system_prompt, connection_ids=connection_ids)

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
            recommendation=f.recommendation, source=f.source, status=f.status,
            created_at=str(f.created_at)
        ) for f in findings
    ]


@router.patch("/findings/{finding_id}/status")
def update_finding_status(
    finding_id: str,
    body: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    finding = session.exec(select(AuditFinding).where(AuditFinding.id == finding_id)).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    project = session.exec(select(Project).where(Project.id == finding.project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Finding not found")
    new_status = body.get("status")
    if new_status not in ("open", "fixed", "ignored"):
        raise HTTPException(status_code=422, detail="status must be 'open', 'fixed', or 'ignored'")
    finding.status = new_status
    session.add(finding)
    session.commit()

    # When marked as Fixed, confirm this solution in the global knowledge base
    if new_status == "fixed":
        try:
            from app.rag.global_indexer import index_findings
            index_findings([finding], session, confirmed=True)
        except Exception:
            pass

    session.refresh(finding)
    return FindingResponse(
        id=finding.id, project_id=finding.project_id, severity=finding.severity,
        category=finding.category, title=finding.title, description=finding.description,
        recommendation=finding.recommendation, source=finding.source, status=finding.status,
        created_at=str(finding.created_at)
    )


@router.get("/runs/{project_id}")
def get_audit_runs(
    project_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from app.models.db import AuditRun
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    runs = session.exec(
        select(AuditRun).where(AuditRun.project_id == project_id).order_by(AuditRun.created_at)
    ).all()
    return [
        {"id": r.id, "health_score": r.health_score, "total_findings": r.total_findings,
         "summary": r.summary, "created_at": str(r.created_at)}
        for r in runs
    ]


@router.post("/run/{project_id}/stream")
async def run_audit_stream(
    project_id: str,
    body: AuditRunOptions = AuditRunOptions(),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return StreamingResponse(
        _audit_stream(project_id, session, connection_ids=body.connection_ids),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _audit_stream(project_id: str, session: Session, connection_ids: list[str] | None = None) -> AsyncIterator[str]:
    def sse(event: dict) -> str:
        return f"data: {json.dumps(event)}\n\n"

    try:
        from app.audit.rules.api import missing_auth, wrong_verb, duplicate_endpoint
        from app.audit.rules.database import missing_index, sensitive_column
        from app.audit.rules.security import sensitive_response, exposed_token
        from app.audit.rules.performance import missing_pagination, large_table_no_index
        from app.models.db import ApiEndpoint, DbTable, UserCredential
        from app.reports.generator import generate_report
        from app.rag.embeddings import index_project

        # Step 1: clear old findings (snapshot ignored first)
        yield sse({"type": "step", "text": "Clearing previous findings..."})
        old_findings_snap = session.exec(select(AuditFinding).where(AuditFinding.project_id == project_id)).all()
        _ignored_titles = {f.title for f in old_findings_snap if f.status == "ignored"}
        for f in old_findings_snap:
            session.delete(f)
        session.commit()

        # Step 2: load data
        ep_q = select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)
        tbl_q = select(DbTable).where(DbTable.project_id == project_id)
        if connection_ids:
            ep_q = ep_q.where(ApiEndpoint.connection_id.in_(connection_ids))
            tbl_q = tbl_q.where(DbTable.connection_id.in_(connection_ids))
        endpoints = list(session.exec(ep_q).all())
        tables = list(session.exec(tbl_q).all())
        yield sse({"type": "step", "text": f"Loaded {len(endpoints)} endpoints and {len(tables)} tables"})

        # Load project context for AI memory
        from app.models.db import Project as ProjectModel
        _project = session.exec(select(ProjectModel).where(ProjectModel.id == project_id)).first()
        _project_context = dict(_project.context_json or {}) if _project else {}

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
        for rule in [sensitive_response, exposed_token]:
            found = rule.check(endpoints, project_id)
            all_findings += found
            yield sse({"type": "rule", "rule": rule.__name__.split(".")[-1], "count": len(found)})

        # Step 6: Performance rules
        yield sse({"type": "step", "text": "Running performance rules...", "group": True})
        for rule, data in [(missing_pagination, endpoints), (large_table_no_index, tables)]:
            found = rule.check(data, project_id)
            all_findings += found
            yield sse({"type": "rule", "rule": rule.__name__.split(".")[-1], "count": len(found)})

        # Step 7: save
        yield sse({"type": "step", "text": f"Saving {len(all_findings)} findings..."})
        for f in all_findings:
            session.add(f)
        session.commit()

        # Restore ignored status
        for f in all_findings:
            if f.title in _ignored_titles:
                f.status = "ignored"
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
    from app.models.db import UserCredential
    credential = session.exec(
        select(UserCredential).where(UserCredential.user_id == current_user.id, UserCredential.is_active == True)
    ).first()
    result = await AuditorAgent(project_id, session, credential).prioritize_findings()
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
    project = session.exec(select(Project).where(Project.id == finding.project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Finding not found")
    from app.agents.advisor_agent import AdvisorAgent
    from app.models.db import UserCredential
    credential = session.exec(
        select(UserCredential).where(UserCredential.user_id == current_user.id, UserCredential.is_active == True)
    ).first()
    result = await AdvisorAgent(finding.project_id, session, credential).get_recommendations(finding_id)
    return AdviceResponse(**result)
