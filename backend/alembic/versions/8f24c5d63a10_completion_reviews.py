"""Completed engagements and two-sided reviews.

Revision ID: 8f24c5d63a10
Revises: f5a1e0d701aa
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '8f24c5d63a10'
down_revision = 'f5a1e0d701aa'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('completion_confirmations',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('match_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('matches.id',ondelete='CASCADE'),nullable=False),
        sa.Column('user_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('confirmed_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint('match_id','user_id',name='uq_completion_match_user'))
    op.create_index('ix_completion_confirmations_match_id','completion_confirmations',['match_id'])
    op.create_table('reviews',
        sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),
        sa.Column('match_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('matches.id',ondelete='CASCADE'),nullable=False),
        sa.Column('reviewer_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('reviewee_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),
        sa.Column('stars',sa.Integer(),nullable=False),
        sa.Column('comment',sa.String(length=1000),nullable=True),
        sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),
        sa.UniqueConstraint('match_id','reviewer_id',name='uq_reviews_match_reviewer'),
        sa.CheckConstraint('stars >= 1 AND stars <= 5',name='ck_reviews_stars'),
        sa.CheckConstraint('reviewer_id <> reviewee_id',name='ck_reviews_distinct_users'))
    op.create_index('ix_reviews_match_id','reviews',['match_id'])
    op.create_index('ix_reviews_reviewee_id','reviews',['reviewee_id'])

def downgrade():
    op.drop_index('ix_reviews_reviewee_id',table_name='reviews')
    op.drop_index('ix_reviews_match_id',table_name='reviews')
    op.drop_table('reviews')
    op.drop_index('ix_completion_confirmations_match_id',table_name='completion_confirmations')
    op.drop_table('completion_confirmations')
