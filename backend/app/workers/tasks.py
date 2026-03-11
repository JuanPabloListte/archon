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


def run_audit_task(project_id: str):
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

            before_count = len(findings)
            findings = asyncio.run(ai_review(
                project_id=project_id,
                findings=findings,
                endpoints=list(endpoints),
                tables=list(tables),
                session=session,
                credential=credential,
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
