from app.workers.celery_app import celery_app
from app.database import engine
from sqlmodel import Session, select
from app.models.db import ProjectConnection

def run_ingestion(connection_id: str):
    with Session(engine) as session:
        conn = session.exec(select(ProjectConnection).where(ProjectConnection.id == connection_id)).first()
        if not conn:
            return

        config = conn.config_json or {}

        if conn.type == "openapi":
            import asyncio
            from app.services.openapi_parser import parse_openapi, parse_openapi_content
            url = config.get("url")
            content = config.get("content")
            headers = config.get("headers", {})
            if url:
                asyncio.run(parse_openapi(url, conn.project_id, session, headers))
            elif content:
                parse_openapi_content(content, conn.project_id, session)

        elif conn.type == "database":
            from app.services.db_analyzer import analyze_database
            db_url = config.get("connection_string")
            if db_url:
                analyze_database(db_url, conn.project_id, session)

@celery_app.task(name="app.workers.tasks.ingest_connection_task")
def ingest_connection_task(connection_id: str):
    run_ingestion(connection_id)

def run_audit_task(project_id: str):
    with Session(engine) as session:
        from app.audit.engine import run_audit
        from app.reports.generator import generate_report
        from app.rag.embeddings import index_project

        findings = run_audit(project_id, session)
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
