"""add status field to audit_findings

Revision ID: 006
Revises: 005
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('audit_findings', sa.Column('status', sa.String(), nullable=False, server_default='open'))


def downgrade():
    op.drop_column('audit_findings', 'status')
