"""Add threaded replies to UnitMessage

Revision ID: e4efc1f60596
Revises: 213640e2dac4
Create Date: 2025-06-20 13:57:44.905987
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4efc1f60596'
down_revision = '213640e2dac4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('unit_messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_unitmessage_parent',  # ✅ Add constraint name
            'unit_messages',
            ['parent_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade():
    with op.batch_alter_table('unit_messages', schema=None) as batch_op:
        batch_op.drop_constraint('fk_unitmessage_parent', type_='foreignkey')  # ✅ Match the name
        batch_op.drop_column('parent_id')