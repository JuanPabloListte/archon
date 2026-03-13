"""add api_keys table

Revision ID: 010
Revises: 009
Create Date: 2026-03-13
"""
from alembic import op

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id VARCHAR NOT NULL,
            user_id VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            key_hash VARCHAR NOT NULL,
            key_prefix VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            last_used_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(key_hash)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_user_id ON api_keys (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys (key_hash)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS api_keys")
