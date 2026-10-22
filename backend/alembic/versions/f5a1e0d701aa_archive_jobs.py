"""Add non-destructive job archival timestamp.

Revision ID: f5a1e0d701aa
Revises: e41a9b7c620d
"""
from alembic import op
import sqlalchemy as sa

revision = 'f5a1e0d701aa'
down_revision = 'e41a9b7c620d'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('jobs', sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column('jobs', 'archived_at')
