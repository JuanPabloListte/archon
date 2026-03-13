"""add global_knowledge table

Revision ID: 008
Revises: 007
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'global_knowledge',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('solution', sa.Text(), nullable=False),
        sa.Column('confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('embedding', sa.Text(), nullable=True),  # pgvector adds this
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    # Add the pgvector column separately
    op.execute("ALTER TABLE global_knowledge ADD COLUMN IF NOT EXISTS embedding vector(768)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_global_knowledge_category ON global_knowledge (category)")


def downgrade():
    op.drop_table('global_knowledge')
