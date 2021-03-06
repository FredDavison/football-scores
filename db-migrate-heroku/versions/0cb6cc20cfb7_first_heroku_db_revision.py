"""First heroku db revision

Revision ID: 0cb6cc20cfb7
Revises: 
Create Date: 2018-04-10 13:28:39.512327

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cb6cc20cfb7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('short_name', sa.String(), nullable=True),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('competitions', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('competitions', sa.Column('games_in_season', sa.Integer(), nullable=True))
    op.add_column('competitions', sa.Column('shortcode', sa.String(), nullable=True))
    op.add_column('competitions', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('competitions', sa.Column('teams_in_competition', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('competitions', 'teams_in_competition')
    op.drop_column('competitions', 'start_date')
    op.drop_column('competitions', 'shortcode')
    op.drop_column('competitions', 'games_in_season')
    op.drop_column('competitions', 'end_date')
    op.drop_table('teams')
    # ### end Alembic commands ###
