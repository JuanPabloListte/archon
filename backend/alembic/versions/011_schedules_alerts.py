"""add audit_schedules and alert_events tables

Revision ID: 011
Revises: 010
Create Date: 2026-03-13
"""
from alembic import op

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_schedules (
            id VARCHAR NOT NULL,
            project_id VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            frequency VARCHAR NOT NULL DEFAULT 'weekly',
            cron_expression VARCHAR,
            hour_utc INTEGER NOT NULL DEFAULT 9,
            day_of_week INTEGER,
            alert_email VARCHAR,
            alert_webhook_url VARCHAR,
            health_score_threshold FLOAT NOT NULL DEFAULT 70.0,
            alert_on_critical BOOLEAN NOT NULL DEFAULT true,
            last_run_at TIMESTAMP,
            next_run_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_schedules_project_id ON audit_schedules (project_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS alert_events (
            id VARCHAR NOT NULL,
            project_id VARCHAR NOT NULL,
            schedule_id VARCHAR NOT NULL,
            trigger_type VARCHAR NOT NULL,
            health_score FLOAT NOT NULL,
            critical_count INTEGER NOT NULL DEFAULT 0,
            notification_sent VARCHAR NOT NULL DEFAULT 'none',
            success BOOLEAN NOT NULL DEFAULT true,
            error_message TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(schedule_id) REFERENCES audit_schedules(id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_alert_events_project_id ON alert_events (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alert_events_schedule_id ON alert_events (schedule_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS alert_events")
    op.execute("DROP TABLE IF EXISTS audit_schedules")
