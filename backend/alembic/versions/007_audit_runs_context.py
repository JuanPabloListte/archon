"""add audit_runs table and project context_json

Revision ID: 007
Revises: 006
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade():
    from alembic import op as _op
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_tables = inspector.get_table_names()
    if 'audit_runs' not in existing_tables:
        op.create_table('audit_runs',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('health_score', sa.Float(), nullable=False, server_default='0'),
            sa.Column('total_findings', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('summary', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
            sa.PrimaryKeyConstraint('id'),
        )

    existing_indexes = [idx['name'] for idx in inspector.get_indexes('audit_runs')] if 'audit_runs' in existing_tables else []
    if 'ix_audit_runs_project_id' not in existing_indexes:
        op.create_index('ix_audit_runs_project_id', 'audit_runs', ['project_id'])

    project_columns = [col['name'] for col in inspector.get_columns('projects')]
    if 'context_json' not in project_columns:
        op.add_column('projects', sa.Column('context_json', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('projects', 'context_json')
    op.drop_index('ix_audit_runs_project_id', table_name='audit_runs')
    op.drop_table('audit_runs')
