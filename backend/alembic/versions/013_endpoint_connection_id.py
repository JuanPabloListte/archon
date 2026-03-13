"""add connection_id to api_endpoints and db_tables

Revision ID: 013
Revises: 012
Create Date: 2026-03-13
"""
from alembic import op

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE api_endpoints ADD COLUMN IF NOT EXISTS connection_id VARCHAR")
    op.execute("ALTER TABLE db_tables ADD COLUMN IF NOT EXISTS connection_id VARCHAR")

def downgrade():
    op.execute("ALTER TABLE api_endpoints DROP COLUMN IF EXISTS connection_id")
    op.execute("ALTER TABLE db_tables DROP COLUMN IF EXISTS connection_id")
