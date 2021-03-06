"""db change

Revision ID: a4fafc68729f
Revises: c8f9da463fd4
Create Date: 2020-02-17 13:47:06.741412

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a4fafc68729f'
down_revision = 'c8f9da463fd4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Indicators', 'description')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Indicators', sa.Column('description', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
