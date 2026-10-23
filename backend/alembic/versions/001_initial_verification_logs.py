"""001_initial_verification_logs

Revision ID: 001_initial_logs
Revises: 
Create Date: 2026-10-22 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_logs'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'verification_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('overall_status', sa.String(length=32), nullable=False),
        sa.Column('processing_mode', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_verification_logs_session_id'), 'verification_logs', ['session_id'], unique=False)
    op.create_index(op.f('ix_verification_logs_scheme_id'), 'verification_logs', ['scheme_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_verification_logs_scheme_id'), table_name='verification_logs')
    op.drop_index(op.f('ix_verification_logs_session_id'), table_name='verification_logs')
    op.drop_table('verification_logs')
