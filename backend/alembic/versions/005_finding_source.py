"""add source field to audit_findings

Revision ID: 005
Revises: 004
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('audit_findings', sa.Column('source', sa.String(), nullable=False, server_default='rule'))


def downgrade():
    op.drop_column('audit_findings', 'source')
