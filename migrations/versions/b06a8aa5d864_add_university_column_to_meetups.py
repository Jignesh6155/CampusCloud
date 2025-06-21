
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b06a8aa5d864'
down_revision = '865e1a34ecc9'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('meetups', schema=None) as batch_op:
        batch_op.add_column(sa.Column('university', sa.String(length=100), nullable=True))  # ✅ allow nulls

def downgrade():
    with op.batch_alter_table('meetups', schema=None) as batch_op:
        batch_op.drop_column('university')
