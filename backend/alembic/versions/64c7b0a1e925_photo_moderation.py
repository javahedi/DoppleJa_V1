"""Photo reports and reversible photo hiding.

Revision ID: 64c7b0a1e925
Revises: 8f24c5d63a10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '64c7b0a1e925'
down_revision = '8f24c5d63a10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('photo_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('reporter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('photo_name', sa.String(32), nullable=False),
        sa.Column('reason', sa.String(32), nullable=False),
        sa.Column('explanation', sa.String(500)),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('reporter_id', 'photo_name', name='uq_photo_reports_reporter_photo'),
        sa.CheckConstraint("status IN ('open', 'reviewed')", name='ck_photo_reports_status'),
    )
    op.create_index('ix_photo_reports_date', 'photo_reports', ['reporter_id', 'created_at'])
    op.create_index('ix_photo_reports_queue', 'photo_reports', ['status', 'photo_name'])
    op.create_table('photo_moderation',
        sa.Column('photo_name', sa.String(32), primary_key=True),
        sa.Column('hidden', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('reason', sa.String(500), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('photo_moderation')
    op.drop_index('ix_photo_reports_queue', table_name='photo_reports')
    op.drop_index('ix_photo_reports_date', table_name='photo_reports')
    op.drop_table('photo_reports')
