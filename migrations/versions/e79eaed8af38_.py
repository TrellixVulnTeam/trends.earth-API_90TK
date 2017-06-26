"""empty message

Revision ID: e79eaed8af38
Revises: 50330e9cf885
Create Date: 2017-06-02 09:45:50.872425

"""
from alembic import op
import sqlalchemy as sa
import datetime

# revision identifiers, used by Alembic.
revision = 'e79eaed8af38'
down_revision = '50330e9cf885'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('script', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=str(datetime.datetime.utcnow())))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=str(datetime.datetime.utcnow())))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'updated_at')
    op.drop_column('script', 'updated_at')
    # ### end Alembic commands ###
