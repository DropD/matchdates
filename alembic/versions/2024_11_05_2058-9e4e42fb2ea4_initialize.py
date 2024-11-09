"""initialize

Revision ID: 9e4e42fb2ea4
Revises: 
Create Date: 2024-11-05 20:58:19.033507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e4e42fb2ea4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('club',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_club')),
    sa.UniqueConstraint('name', name=op.f('uq_club_name'))
    )
    op.create_table('location',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_location')),
    sa.UniqueConstraint('name', name=op.f('uq_location_name'))
    )
    op.create_table('season',
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_season')),
    sa.UniqueConstraint('url', name=op.f('uq_season_url'))
    )
    op.create_table('club_season_association',
    sa.Column('club_id', sa.Integer(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['club_id'], ['club.id'], name=op.f('fk_club_season_association_club_id_club')),
    sa.ForeignKeyConstraint(['season_id'], ['season.id'], name=op.f('fk_club_season_association_season_id_season')),
    sa.PrimaryKeyConstraint('club_id', 'season_id', name=op.f('pk_club_season_association'))
    )
    op.create_table('matchdate',
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('date_time', sa.DateTime(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], name=op.f('fk_matchdate_location_id_location')),
    sa.ForeignKeyConstraint(['season_id'], ['season.id'], name=op.f('fk_matchdate_season_id_season')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_matchdate')),
    sa.UniqueConstraint('url', name=op.f('uq_matchdate_url'))
    )
    op.create_table('team',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('team_nr', sa.Integer(), nullable=False),
    sa.Column('club_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['club_id'], ['club.id'], name=op.f('fk_team_club_id_club')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_team')),
    sa.UniqueConstraint('name', name=op.f('uq_team_name'))
    )
    op.create_table('matchdate_away_team_assoc',
    sa.Column('match_date_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['match_date_id'], ['matchdate.id'], name=op.f('fk_matchdate_away_team_assoc_match_date_id_matchdate')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_matchdate_away_team_assoc_team_id_team')),
    sa.PrimaryKeyConstraint('match_date_id', 'team_id', name=op.f('pk_matchdate_away_team_assoc'))
    )
    op.create_table('matchdate_changelog',
    sa.Column('match_date_id', sa.Integer(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('date_time', sa.DateTime(), nullable=False),
    sa.Column('archived_date_time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], name=op.f('fk_matchdate_changelog_location_id_location')),
    sa.ForeignKeyConstraint(['match_date_id'], ['matchdate.id'], name=op.f('fk_matchdate_changelog_match_date_id_matchdate')),
    sa.PrimaryKeyConstraint('match_date_id', 'location_id', 'date_time', name=op.f('pk_matchdate_changelog'))
    )
    op.create_table('matchdate_home_team_assoc',
    sa.Column('match_date_id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['match_date_id'], ['matchdate.id'], name=op.f('fk_matchdate_home_team_assoc_match_date_id_matchdate')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_matchdate_home_team_assoc_team_id_team')),
    sa.PrimaryKeyConstraint('match_date_id', 'team_id', name=op.f('pk_matchdate_home_team_assoc'))
    )
    op.create_table('team_season_assoc',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['season_id'], ['season.id'], name=op.f('fk_team_season_assoc_season_id_season')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_team_season_assoc_team_id_team')),
    sa.PrimaryKeyConstraint('team_id', 'season_id', name=op.f('pk_team_season_assoc'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('team_season_assoc')
    op.drop_table('matchdate_home_team_assoc')
    op.drop_table('matchdate_changelog')
    op.drop_table('matchdate_away_team_assoc')
    op.drop_table('team')
    op.drop_table('matchdate')
    op.drop_table('club_season_association')
    op.drop_table('season')
    op.drop_table('location')
    op.drop_table('club')
    # ### end Alembic commands ###
