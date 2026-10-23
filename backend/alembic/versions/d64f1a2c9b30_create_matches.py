"""Create matches; backfill previously mutual likes.

Revision ID: d64f1a2c9b30
Revises: 7c91d4e5a602
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'd64f1a2c9b30'
down_revision = '7c91d4e5a602'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('worker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('worker_profiles.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('job_id', 'worker_id', name='uq_matches_job_worker'),
    )
    op.create_index('ix_matches_job_id', 'matches', ['job_id'])
    op.create_index('ix_matches_worker_id', 'matches', ['worker_id'])

    # PostGIS tables remain untouched. PostgreSQL 16 provides gen_random_uuid().
    # Backfill all already-existing worker/job pairs where BOTH parties liked.
    op.execute("""
        INSERT INTO matches (id, job_id, worker_id, created_at)
        SELECT gen_random_uuid(), w.job_id, w.worker_id,
               GREATEST(w.created_at, e.created_at)
        FROM swipes AS w
        JOIN swipes AS e
          ON e.job_id = w.job_id
         AND e.worker_id = w.worker_id
         AND e.actor_role = 'employer'
         AND e.action = 'like'
        WHERE w.actor_role = 'worker'
          AND w.action = 'like'
        ON CONFLICT (job_id, worker_id) DO NOTHING
    """)


def downgrade():
    op.drop_index('ix_matches_worker_id', table_name='matches')
    op.drop_index('ix_matches_job_id', table_name='matches')
    op.drop_table('matches')
