"""add custom_rules table

Revision ID: 012
Revises: 011
Create Date: 2026-03-13
"""
from alembic import op

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS custom_rules (
            id VARCHAR NOT NULL,
            project_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            description TEXT,
            category VARCHAR NOT NULL DEFAULT 'security',
            severity VARCHAR NOT NULL DEFAULT 'medium',
            target VARCHAR NOT NULL DEFAULT 'endpoints',
            rule_yaml TEXT NOT NULL,
            rule_json JSON,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_custom_rules_project_id ON custom_rules (project_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS custom_rules")
