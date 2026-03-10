from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from pydantic import BaseModel
from app.database import get_session
from app.models.db import User, Project, AuditFinding, Report
from app.api.deps import get_current_user

router = APIRouter()


class DashboardStats(BaseModel):
    total_projects: int
    total_findings: int
    avg_health_score: float | None
    projects_audited: int


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    projects = session.exec(
        select(Project).where(Project.owner_id == current_user.id)
    ).all()
    project_ids = [p.id for p in projects]

    total_findings = 0
    health_scores: list[float] = []

    if project_ids:
        total_findings = session.exec(
            select(func.count(AuditFinding.id)).where(
                AuditFinding.project_id.in_(project_ids)
            )
        ).one()

        for pid in project_ids:
            latest = session.exec(
                select(Report)
                .where(Report.project_id == pid)
                .order_by(Report.created_at.desc())
            ).first()
            if latest:
                health_scores.append(latest.health_score)

    avg_health = round(sum(health_scores) / len(health_scores), 1) if health_scores else None

    return DashboardStats(
        total_projects=len(projects),
        total_findings=total_findings,
        avg_health_score=avg_health,
        projects_audited=len(health_scores),
    )
