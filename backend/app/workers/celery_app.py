from celery import Celery
from celery.schedules import crontab
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
        "app.workers.tasks.run_audit_celery_task": {"queue": "audit"},
        "app.workers.tasks.generate_report_task": {"queue": "reports"},
        "app.workers.tasks.dispatch_scheduled_audits": {"queue": "scheduled"},
        "app.workers.tasks.run_scheduled_audit": {"queue": "scheduled"},
    },
    beat_schedule={
        "dispatch-scheduled-audits": {
            "task": "app.workers.tasks.dispatch_scheduled_audits",
            "schedule": crontab(minute=0),  # every hour on the hour
        },
    },
)
