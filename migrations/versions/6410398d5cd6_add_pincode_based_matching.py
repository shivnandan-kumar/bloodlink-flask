"""Add pincode based matching

Revision ID: 6410398d5cd6
Revises: 2a0e620351a0
Create Date: 2026-06-26 18:52:42.632803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6410398d5cd6'
down_revision = '2a0e620351a0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('blood_request', sa.Column('pincode', sa.String(length=6), nullable=True))
    op.create_index(op.f('ix_blood_request_pincode'), 'blood_request', ['pincode'], unique=False)
    op.add_column('user', sa.Column('pincode', sa.String(length=6), nullable=True))
    op.create_index(op.f('ix_user_pincode'), 'user', ['pincode'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_user_pincode'), table_name='user')
    op.drop_column('user', 'pincode')
    op.drop_index(op.f('ix_blood_request_pincode'), table_name='blood_request')
    op.drop_column('blood_request', 'pincode')
