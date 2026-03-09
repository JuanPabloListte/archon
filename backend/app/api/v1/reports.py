from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel
from app.database import get_session
from app.models.db import User, Project, Report
from app.api.deps import get_current_user

router = APIRouter()

class ReportResponse(BaseModel):
    id: str
    project_id: str
    health_score: float
    summary: str | None
    report_json: dict | None
    created_at: str

@router.get("/{project_id}", response_model=List[ReportResponse])
def get_reports(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    reports = session.exec(select(Report).where(Report.project_id == project_id)).all()
    return [
        ReportResponse(id=r.id, project_id=r.project_id, health_score=r.health_score,
                      summary=r.summary, report_json=r.report_json, created_at=str(r.created_at))
        for r in reports
    ]

@router.get("/{project_id}/latest", response_model=ReportResponse)
def get_latest_report(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    project = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    report = session.exec(
        select(Report).where(Report.project_id == project_id).order_by(Report.created_at.desc())
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="No reports found")
    return ReportResponse(id=report.id, project_id=report.project_id, health_score=report.health_score,
                         summary=report.summary, report_json=report.report_json, created_at=str(report.created_at))
