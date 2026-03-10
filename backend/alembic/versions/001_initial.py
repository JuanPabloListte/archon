"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # users
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('owner_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])

    # project_connections
    op.create_table(
        'project_connections',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('config_json', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_project_connections_project_id', 'project_connections', ['project_id'])

    # api_endpoints
    op.create_table(
        'api_endpoints',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=False),
        sa.Column('auth_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('parameters', postgresql.JSON(), nullable=True),
        sa.Column('responses', postgresql.JSON(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_api_endpoints_project_id', 'api_endpoints', ['project_id'])

    # db_tables
    op.create_table(
        'db_tables',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('table_name', sa.String(), nullable=False),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('columns', postgresql.JSON(), nullable=True),
        sa.Column('indexes', postgresql.JSON(), nullable=True),
        sa.Column('foreign_keys', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_db_tables_project_id', 'db_tables', ['project_id'])

    # audit_findings
    op.create_table(
        'audit_findings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('recommendation', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_findings_project_id', 'audit_findings', ['project_id'])

    # embeddings
    op.create_table(
        'embeddings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.String(), nullable=False),  # handled by pgvector at DDL level
    )
    op.create_index('ix_embeddings_project_id', 'embeddings', ['project_id'])
    # Replace the string column with the actual vector type
    op.execute("ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector(768) USING embedding::vector")

    # reports
    op.create_table(
        'reports',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('report_json', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_reports_project_id', 'reports', ['project_id'])


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('embeddings')
    op.drop_table('audit_findings')
    op.drop_table('db_tables')
    op.drop_table('api_endpoints')
    op.drop_table('project_connections')
    op.drop_table('projects')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS vector")
