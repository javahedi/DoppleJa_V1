"""Add profession to worker profiles.

Revision ID: c84d20e5b319
Revises: b39a2fe461c0
"""
from alembic import op
import sqlalchemy as sa
revision = "c84d20e5b319"
down_revision = "b39a2fe461c0"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("worker_profiles", sa.Column("profession", sa.String(length=100), nullable=True))

def downgrade():
    op.drop_column("worker_profiles", "profession")
