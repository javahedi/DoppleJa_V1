"""Create profiles for private and business employers.

Revision ID: f81c6e2a074b
Revises: c84d20e5b319
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f81c6e2a074b"
down_revision = "c84d20e5b319"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "employer_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("employer_type", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("employer_type IN ('private', 'business')", name="ck_employer_type"),
    )


def downgrade():
    op.drop_table("employer_profiles")
