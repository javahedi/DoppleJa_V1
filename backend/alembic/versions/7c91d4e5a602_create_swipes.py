"""Create worker-job like/pass swipes, without matches yet.

Revision ID: 7c91d4e5a602
Revises: a9f8b2c3d401
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '7c91d4e5a602'
down_revision = 'a9f8b2c3d401'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('swipes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker_profiles.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_role', sa.String(20), nullable=False),
        sa.Column('action', sa.String(8), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("actor_role IN ('worker','employer')", name='ck_swipes_actor_role'),
        sa.CheckConstraint("action IN ('like','pass')", name='ck_swipes_action'),
        sa.UniqueConstraint('job_id','worker_id','actor_role',name='uq_swipe_pair_actor'),
    )
    op.create_index('ix_swipes_job_id', 'swipes', ['job_id'])
    op.create_index('ix_swipes_worker_id', 'swipes', ['worker_id'])

def downgrade():
    op.drop_index('ix_swipes_worker_id', table_name='swipes')
    op.drop_index('ix_swipes_job_id', table_name='swipes')
    op.drop_table('swipes')
