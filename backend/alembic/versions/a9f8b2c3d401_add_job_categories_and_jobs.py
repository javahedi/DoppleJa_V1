"""Add simple job categories and listings.

Revision ID: a9f8b2c3d401
Revises: f81c6e2a074b
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a9f8b2c3d401'
down_revision = 'f81c6e2a074b'
branch_labels = None
depends_on = None

CATEGORIES = [
    (1, 'restaurant-cafe', 'Restaurant & Café'),
    (2, 'hospital-care', 'Krankenhaus & Pflege'),
    (3, 'drivers-logistics', 'Fahrer & Logistik'),
    (4, 'handwerker', 'Handwerk'),
    (5, 'painting-construction', 'Maler & Bau'),
    (6, 'cleaning', 'Reinigung'),
    (7, 'daily-event', 'Tagesjobs & Events'),
    (8, 'retail', 'Einzelhandel'),
    (9, 'other', 'Sonstiges'),
]

def upgrade():
    categories = op.create_table('job_categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(60), nullable=False, unique=True),
        sa.Column('name', sa.String(100), nullable=False),
    )
    op.bulk_insert(categories, [dict(id=i, slug=s, name=n) for i,s,n in CATEGORIES])
    op.create_table('jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employer_profiles.user_id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('job_categories.id'), nullable=False),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('work_type', sa.String(20), nullable=False),
        sa.Column('hourly_pay_min', sa.Numeric(8,2), nullable=True),
        sa.Column('hourly_pay_max', sa.Numeric(8,2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("work_type IN ('minijob', 'part_time', 'full_time', 'temporary')", name='ck_jobs_work_type'),
        sa.CheckConstraint('hourly_pay_min IS NULL OR hourly_pay_min >= 0', name='ck_jobs_min_pay'),
        sa.CheckConstraint('hourly_pay_max IS NULL OR hourly_pay_max >= 0', name='ck_jobs_max_pay'),
        sa.CheckConstraint('hourly_pay_min IS NULL OR hourly_pay_max IS NULL OR hourly_pay_max >= hourly_pay_min', name='ck_jobs_pay_range'),
    )
    op.create_index('ix_jobs_employer_id', 'jobs', ['employer_id'])
    op.create_index('ix_jobs_category_id', 'jobs', ['category_id'])
    op.create_index('ix_jobs_city', 'jobs', ['city'])

def downgrade():
    op.drop_index('ix_jobs_city', 'jobs')
    op.drop_index('ix_jobs_category_id', 'jobs')
    op.drop_index('ix_jobs_employer_id', 'jobs')
    op.drop_table('jobs')
    op.drop_table('job_categories')
