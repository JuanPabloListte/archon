"""Webhook alert notifications via HTTP POST."""
import logging
from datetime import datetime
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


def send_webhook(
    url: str,
    project_id: str,
    project_name: str,
    health_score: float,
    critical_count: int,
    high_count: int,
    total_findings: int,
) -> bool:
    payload = {
        "event": "audit_alert",
        "project_id": project_id,
        "project_name": project_name,
        "health_score": health_score,
        "findings": {
            "total": total_findings,
            "critical": critical_count,
            "high": high_count,
        },
        "report_url": f"{settings.FRONTEND_URL}/projects/{project_id}/report",
        "triggered_at": datetime.utcnow().isoformat(),
    }
    try:
        r = httpx.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logger.info(f"Webhook delivered to {url} for project '{project_name}'")
        return True
    except Exception as e:
        logger.error(f"Webhook delivery failed to {url}: {e}")
        return False
