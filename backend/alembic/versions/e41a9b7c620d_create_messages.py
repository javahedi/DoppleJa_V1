"""Create text messages for existing matches.

Revision ID: e41a9b7c620d
Revises: d64f1a2c9b30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e41a9b7c620d'
down_revision = 'd64f1a2c9b30'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.String(length=2000), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_messages_match_created', 'messages', ['match_id', 'created_at', 'id'])

def downgrade():
    op.drop_index('ix_messages_match_created', table_name='messages')
    op.drop_table('messages')
