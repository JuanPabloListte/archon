"""add audit_system_prompt to projects

Revision ID: 009
Revises: 008
Create Date: 2026-03-13

"""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('audit_system_prompt', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('projects', 'audit_system_prompt')
