"""add google oauth fields

Revision ID: 002
Revises: 001
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('users', 'password_hash', existing_type=sa.String(), nullable=True)
    op.add_column('users', sa.Column('google_id', sa.String(), nullable=True))
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=False)


def downgrade():
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'google_id')
    op.alter_column('users', 'password_hash', existing_type=sa.String(), nullable=False)
