"""Add anonymous flag to meetups

Revision ID: c419dd1f4c90
Revises: b06a8aa5d864
Create Date: 2025-06-22 09:15:57.927678
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c419dd1f4c90'
down_revision = 'b06a8aa5d864'
branch_labels = None
depends_on = None


def upgrade():
    # ✅ Add anonymous column only, do NOT alter university nullability
    with op.batch_alter_table('meetups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('anonymous', sa.Boolean(), nullable=True))
        # batch_op.alter_column('university',
        #        existing_type=sa.VARCHAR(length=100),
        #        nullable=False)


def downgrade():
    with op.batch_alter_table('meetups', schema=None) as batch_op:
        # This is safe to leave as-is since it reverts only your change
        batch_op.drop_column('anonymous')
        # batch_op.alter_column('university',
        #        existing_type=sa.VARCHAR(length=100),
        #        nullable=True)