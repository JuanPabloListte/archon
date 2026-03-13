"""Email alert notifications via SMTP."""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger(__name__)


def send_alert_email(
    to: str,
    project_name: str,
    health_score: float,
    critical_count: int,
    high_count: int,
    project_url: str = "",
) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP not configured — skipping email alert")
        return False

    score_color = "#22c55e" if health_score >= 80 else "#eab308" if health_score >= 60 else "#ef4444"
    subject = f"[Archon] Audit Alert — {project_name} (score: {health_score:.0f}/100)"

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:24px;background:#0f0f0f;color:#e5e5e5;border-radius:12px">
      <h2 style="margin:0 0 16px;color:#a78bfa">Archon Audit Alert</h2>
      <p style="color:#a1a1aa;margin:0 0 20px">An automated audit was completed for <strong style="color:#e5e5e5">{project_name}</strong> and requires your attention.</p>

      <div style="background:#1a1a1a;border-radius:8px;padding:16px;margin-bottom:20px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <span style="font-size:32px;font-weight:700;color:{score_color}">{health_score:.0f}</span>
          <span style="color:#a1a1aa;font-size:14px">/100 Health Score</span>
        </div>
        <div style="display:flex;gap:16px">
          <span style="color:#ef4444;font-size:13px">🔴 {critical_count} Critical</span>
          <span style="color:#f97316;font-size:13px">🟠 {high_count} High</span>
        </div>
      </div>

      {"<a href='" + project_url + "' style='display:inline-block;background:#7c3aed;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px'>View Report →</a>" if project_url else ""}

      <p style="color:#52525b;font-size:12px;margin-top:24px">
        You received this because you have scheduled audits enabled for this project.
      </p>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to, msg.as_string())

        logger.info(f"Alert email sent to {to} for project '{project_name}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False
