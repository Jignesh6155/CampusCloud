"""Add GeneralMessage model

Revision ID: 99caefb59fb6
Revises: 31ce5371a50e
Create Date: 2025-06-18 19:21:34.835170

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99caefb59fb6'
down_revision = '31ce5371a50e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('general_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('general_messages')
    # ### end Alembic commands ###
