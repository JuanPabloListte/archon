from celery import Celery
from app.config import settings

celery_app = Celery(
    "archon",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.workers.tasks.ingest_connection_task": {"queue": "ingestion"},
        "app.workers.tasks.run_audit_task": {"queue": "audit"},
        "app.workers.tasks.generate_report_task": {"queue": "reports"},
    },
)
