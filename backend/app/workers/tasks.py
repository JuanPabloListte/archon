import logging
from app.workers.celery_app import celery_app
from app.database import engine
from sqlmodel import Session, select
from app.models.db import ProjectConnection

logger = logging.getLogger(__name__)


def _update_connection_status(connection_id: str, status: str, error: str | None = None, count: int | None = None):
    """Persist ingestion status back into config_json so the API can expose it."""
    with Session(engine) as s:
        conn = s.exec(select(ProjectConnection).where(ProjectConnection.id == connection_id)).first()
        if not conn:
            return
        cfg = dict(conn.config_json or {})
        cfg["_status"] = status
        cfg["_error"] = error
        if count is not None:
            cfg["_ingested_count"] = count
        conn.config_json = cfg
        s.add(conn)
        s.commit()


def run_ingestion(connection_id: str):
    with Session(engine) as session:
        conn = session.exec(select(ProjectConnection).where(ProjectConnection.id == connection_id)).first()
        if not conn:
            logger.error(f"Connection {connection_id} not found")
            return

        config = conn.config_json or {}
        _update_connection_status(connection_id, "ingesting")

        try:
            if conn.type == "openapi":
                import asyncio
                from app.services.openapi_parser import parse_openapi, parse_openapi_content
                url = config.get("url")
                content = config.get("content")
                headers = config.get("headers", {})
                if url:
                    count = asyncio.run(parse_openapi(url, conn.project_id, session, headers))
                elif content:
                    count = parse_openapi_content(content, conn.project_id, session)
                else:
                    count = 0
                _update_connection_status(connection_id, "done", count=count or 0)

            elif conn.type == "database":
                from app.services.db_analyzer import analyze_database
                db_url = config.get("connection_string")
                if not db_url:
                    raise ValueError("No connection_string provided in config")
                analyze_database(db_url, conn.project_id, session)
                # count tables ingested
                from sqlmodel import select as sel
                from app.models.db import DbTable
                n = len(session.exec(sel(DbTable).where(DbTable.project_id == conn.project_id)).all())
                _update_connection_status(connection_id, "done", count=n)

            else:
                _update_connection_status(connection_id, "done", count=0)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ingestion failed for connection {connection_id}: {error_msg}", exc_info=True)
            _update_connection_status(connection_id, "error", error=error_msg)


@celery_app.task(name="app.workers.tasks.ingest_connection_task")
def ingest_connection_task(connection_id: str):
    run_ingestion(connection_id)


def run_audit_task(project_id: str, system_prompt: str | None = None):
    import asyncio
    with Session(engine) as session:
        from app.audit.engine import run_audit
        from app.audit.ai_reviewer import ai_review
        from app.reports.generator import generate_report
        from app.rag.embeddings import index_project
        from app.models.db import Project, UserCredential, ApiEndpoint, DbTable
        from sqlmodel import select

        # 1. Rule-based audit
        findings = run_audit(project_id, session)

        # 2. AI review pass (use active credential if available)
        try:
            project = session.get(Project, project_id)
            credential = None
            if project:
                credential = session.exec(
                    select(UserCredential).where(
                        UserCredential.user_id == project.owner_id,
                        UserCredential.is_active == True,
                    )
                ).first()

            if not credential:
                logger.info("AI review skipped: no active credential configured")
            else:
                logger.info(f"Running AI review with: {credential.provider}/{credential.model}")

            endpoints = session.exec(select(ApiEndpoint).where(ApiEndpoint.project_id == project_id)).all()
            tables = session.exec(select(DbTable).where(DbTable.project_id == project_id)).all()

            # Resolve system prompt: per-run override > project setting > default
            resolved_system = (
                system_prompt
                or (project.audit_system_prompt if project else None)
            )

            before_count = len(findings)
            findings = asyncio.run(ai_review(
                project_id=project_id,
                findings=findings,
                endpoints=list(endpoints),
                tables=list(tables),
                session=session,
                credential=credential,
                context=dict(project.context_json or {}) if project else {},
                system_prompt=resolved_system,
            ))
            after_count = len(findings)
            ai_added = sum(1 for f in findings if f.source == "ai")
            dismissed = before_count - (after_count - ai_added)
            logger.info(
                f"AI review complete: {before_count} rule findings → "
                f"{dismissed} dismissed, {ai_added} new AI findings, "
                f"{after_count} total"
            )
        except Exception as e:
            logger.warning(f"AI review step failed, continuing with rule findings: {e}")

        # 3. Generate report + index embeddings
        generate_report(project_id, session)
        index_project(project_id, session)


@celery_app.task(name="app.workers.tasks.run_audit_task")
def run_audit_celery_task(project_id: str):
    run_audit_task(project_id)


@celery_app.task(name="app.workers.tasks.generate_report_task")
def generate_report_task(project_id: str):
    with Session(engine) as session:
        from app.reports.generator import generate_report
        generate_report(project_id, session)


@celery_app.task(name="app.workers.tasks.dispatch_scheduled_audits")
def dispatch_scheduled_audits():
    """Runs every hour — checks which schedules are due and triggers them."""
    from datetime import datetime
    from sqlmodel import select
    from app.models.db import AuditSchedule

    with Session(engine) as session:
        now = datetime.utcnow()
        due = session.exec(
            select(AuditSchedule).where(
                AuditSchedule.is_active == True,
                AuditSchedule.next_run_at <= now,
            )
        ).all()
        for schedule in due:
            run_scheduled_audit.delay(schedule.id)
            # Advance next_run_at immediately to prevent double-dispatch
            from app.api.v1.schedules import _calc_next_run
            schedule.next_run_at = _calc_next_run(
                schedule.frequency, schedule.hour_utc,
                schedule.day_of_week, schedule.cron_expression,
            )
            session.add(schedule)
        session.commit()
        logger.info(f"Scheduled audit dispatcher: {len(due)} job(s) queued")


@celery_app.task(name="app.workers.tasks.run_scheduled_audit")
def run_scheduled_audit(schedule_id: str):
    """Runs a scheduled audit and sends alerts if thresholds are breached."""
    from datetime import datetime
    from sqlmodel import select
    from app.models.db import AuditSchedule, AlertEvent, Project, Report
    from app.notifications.email import send_alert_email
    from app.notifications.webhook import send_webhook

    with Session(engine) as session:
        schedule = session.get(AuditSchedule, schedule_id)
        if not schedule:
            return

        project = session.get(Project, schedule.project_id)
        if not project:
            return

        logger.info(f"Running scheduled audit for project '{project.name}' (schedule {schedule_id})")
        run_audit_task(schedule.project_id)

        report = session.exec(
            select(Report)
            .where(Report.project_id == schedule.project_id)
            .order_by(Report.created_at.desc())
        ).first()

        schedule.last_run_at = datetime.utcnow()
        session.add(schedule)
        session.commit()

        if not report:
            return

        from app.models.db import AuditFinding
        findings = session.exec(
            select(AuditFinding).where(AuditFinding.project_id == schedule.project_id)
        ).all()
        critical_count = sum(1 for f in findings if f.severity == "critical")
        high_count = sum(1 for f in findings if f.severity == "high")

        score_breach = report.health_score < schedule.health_score_threshold
        critical_breach = schedule.alert_on_critical and critical_count > 0

        if not score_breach and not critical_breach:
            return

        trigger = "both" if score_breach and critical_breach else ("health_score_drop" if score_breach else "critical_findings")
        project_url = f"http://localhost:3000/projects/{schedule.project_id}/report"

        email_ok = webhook_ok = True
        errors = []

        if schedule.alert_email:
            email_ok = send_alert_email(
                to=schedule.alert_email,
                project_name=project.name,
                health_score=report.health_score,
                critical_count=critical_count,
                high_count=high_count,
                project_url=project_url,
            )
            if not email_ok:
                errors.append("email delivery failed")

        if schedule.alert_webhook_url:
            webhook_ok = send_webhook(
                url=schedule.alert_webhook_url,
                project_id=project.id,
                project_name=project.name,
                health_score=report.health_score,
                critical_count=critical_count,
                high_count=high_count,
                total_findings=len(findings),
            )
            if not webhook_ok:
                errors.append("webhook delivery failed")

        notification_sent = "none"
        if schedule.alert_email and schedule.alert_webhook_url:
            notification_sent = "both"
        elif schedule.alert_email:
            notification_sent = "email"
        elif schedule.alert_webhook_url:
            notification_sent = "webhook"

        event = AlertEvent(
            project_id=schedule.project_id,
            schedule_id=schedule_id,
            trigger_type=trigger,
            health_score=report.health_score,
            critical_count=critical_count,
            notification_sent=notification_sent,
            success=not errors,
            error_message="; ".join(errors) if errors else None,
        )
        session.add(event)
        session.commit()
        logger.info(f"Scheduled audit alert sent: {trigger} for '{project.name}'")
