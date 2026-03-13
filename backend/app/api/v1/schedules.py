"""Scheduled audits — CRUD and alert history."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from typing import Optional
from app.database import get_session
from app.models.db import User, Project, AuditSchedule, AlertEvent
from app.api.deps import get_current_user

router = APIRouter()


class ScheduleCreate(BaseModel):
    frequency: str = "weekly"          # daily | weekly | custom
    cron_expression: Optional[str] = None
    hour_utc: int = 9
    day_of_week: Optional[int] = None  # 0=Mon..6=Sun
    alert_email: Optional[str] = None
    alert_webhook_url: Optional[str] = None
    health_score_threshold: float = 70.0
    alert_on_critical: bool = True


class ScheduleUpdate(BaseModel):
    is_active: Optional[bool] = None
    frequency: Optional[str] = None
    cron_expression: Optional[str] = None
    hour_utc: Optional[int] = None
    day_of_week: Optional[int] = None
    alert_email: Optional[str] = None
    alert_webhook_url: Optional[str] = None
    health_score_threshold: Optional[float] = None
    alert_on_critical: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: str
    project_id: str
    is_active: bool
    frequency: str
    cron_expression: Optional[str]
    hour_utc: int
    day_of_week: Optional[int]
    alert_email: Optional[str]
    alert_webhook_url: Optional[str]
    health_score_threshold: float
    alert_on_critical: bool
    last_run_at: Optional[str]
    next_run_at: Optional[str]
    created_at: str


def _calc_next_run(frequency: str, hour_utc: int, day_of_week: Optional[int], cron_expression: Optional[str]) -> datetime:
    now = datetime.utcnow()
    if frequency == "daily":
        candidate = now.replace(hour=hour_utc, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate
    if frequency == "weekly":
        dow = day_of_week if day_of_week is not None else 0  # default Monday
        days_ahead = (dow - now.weekday()) % 7
        candidate = (now + timedelta(days=days_ahead)).replace(hour=hour_utc, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(weeks=1)
        return candidate
    if frequency == "custom" and cron_expression:
        try:
            from croniter import croniter
            return croniter(cron_expression, now).get_next(datetime)
        except Exception:
            pass
    return now + timedelta(days=1)


def _to_response(s: AuditSchedule) -> ScheduleResponse:
    return ScheduleResponse(
        id=s.id, project_id=s.project_id, is_active=s.is_active,
        frequency=s.frequency, cron_expression=s.cron_expression,
        hour_utc=s.hour_utc, day_of_week=s.day_of_week,
        alert_email=s.alert_email, alert_webhook_url=s.alert_webhook_url,
        health_score_threshold=s.health_score_threshold, alert_on_critical=s.alert_on_critical,
        last_run_at=str(s.last_run_at) if s.last_run_at else None,
        next_run_at=str(s.next_run_at) if s.next_run_at else None,
        created_at=str(s.created_at),
    )


def _get_project_or_404(project_id: str, user: User, session: Session) -> Project:
    p = session.exec(select(Project).where(Project.id == project_id, Project.owner_id == user.id)).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


@router.get("/{project_id}/schedules", response_model=list[ScheduleResponse])
def list_schedules(project_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    schedules = session.exec(select(AuditSchedule).where(AuditSchedule.project_id == project_id)).all()
    return [_to_response(s) for s in schedules]


@router.post("/{project_id}/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(project_id: str, body: ScheduleCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    schedule = AuditSchedule(
        project_id=project_id,
        frequency=body.frequency,
        cron_expression=body.cron_expression,
        hour_utc=body.hour_utc,
        day_of_week=body.day_of_week,
        alert_email=body.alert_email,
        alert_webhook_url=body.alert_webhook_url,
        health_score_threshold=body.health_score_threshold,
        alert_on_critical=body.alert_on_critical,
        next_run_at=_calc_next_run(body.frequency, body.hour_utc, body.day_of_week, body.cron_expression),
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return _to_response(schedule)


@router.patch("/{project_id}/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(project_id: str, schedule_id: str, body: ScheduleUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    schedule = session.exec(select(AuditSchedule).where(AuditSchedule.id == schedule_id, AuditSchedule.project_id == project_id)).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(schedule, field, val)
    schedule.next_run_at = _calc_next_run(schedule.frequency, schedule.hour_utc, schedule.day_of_week, schedule.cron_expression)
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return _to_response(schedule)


@router.delete("/{project_id}/schedules/{schedule_id}", status_code=204)
def delete_schedule(project_id: str, schedule_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    schedule = session.exec(select(AuditSchedule).where(AuditSchedule.id == schedule_id, AuditSchedule.project_id == project_id)).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    session.delete(schedule)
    session.commit()


@router.get("/{project_id}/schedules/{schedule_id}/alerts", response_model=list[dict])
def list_alert_events(project_id: str, schedule_id: str, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    _get_project_or_404(project_id, current_user, session)
    events = session.exec(
        select(AlertEvent).where(AlertEvent.schedule_id == schedule_id).order_by(AlertEvent.created_at.desc())
    ).all()
    return [
        {"id": e.id, "trigger_type": e.trigger_type, "health_score": e.health_score,
         "critical_count": e.critical_count, "notification_sent": e.notification_sent,
         "success": e.success, "error_message": e.error_message, "created_at": str(e.created_at)}
        for e in events
    ]
