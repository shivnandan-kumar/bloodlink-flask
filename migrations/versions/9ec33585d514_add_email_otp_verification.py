"""Add email OTP verification

Revision ID: 9ec33585d514
Revises: c383b93003d8
Create Date: 2026-06-22 21:44:01.460803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ec33585d514'
down_revision = 'c383b93003d8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('is_email_verified', sa.Boolean(), server_default=sa.text('1'), nullable=False))
    op.add_column('user', sa.Column('email_otp_hash', sa.String(length=255), nullable=True))
    op.add_column('user', sa.Column('email_otp_expires_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('email_otp_sent_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('email_otp_attempts', sa.Integer(), server_default=sa.text('0'), nullable=False))


def downgrade():
    op.drop_column('user', 'email_otp_attempts')
    op.drop_column('user', 'email_otp_sent_at')
    op.drop_column('user', 'email_otp_expires_at')
    op.drop_column('user', 'email_otp_hash')
    op.drop_column('user', 'is_email_verified')
