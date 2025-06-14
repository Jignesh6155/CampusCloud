"""Add normalized_name to forums (nullable for now)

Revision ID: 91376e40ecb7
Revises: 30a77e2c73ca
Create Date: 2025-06-14 09:44:13.159365
"""

from alembic import op
import sqlalchemy as sa

revision = '91376e40ecb7'
down_revision = '30a77e2c73ca'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('forums', schema=None) as batch_op:
        batch_op.add_column(sa.Column('normalized_name', sa.String(length=100), nullable=True))  # <== temporarily nullable

def downgrade():
    with op.batch_alter_table('forums', schema=None) as batch_op:
        batch_op.drop_column('normalized_name')