"""empty message

Revision ID: 35d122548309
Revises: 
Create Date: 2025-02-20 16:00:48.710499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35d122548309'
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
    op.create_table('doubles_pair',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_doubles_pair'))
    )
    op.create_table('location',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_location')),
    sa.UniqueConstraint('name', name=op.f('uq_location_name'))
    )
    op.create_table('player',
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_player')),
    sa.UniqueConstraint('url', name=op.f('uq_player_url'))
    )
    op.create_table('season',
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
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
    op.create_table('draw',
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['season_id'], ['season.id'], name=op.f('fk_draw_season_id_season')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_draw')),
    sa.UniqueConstraint('url', 'season_id', name=op.f('uq_draw_url'))
    )
    op.create_table('player_doubles_association',
    sa.Column('pair_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pair_id'], ['doubles_pair.id'], name=op.f('fk_player_doubles_association_pair_id_doubles_pair')),
    sa.ForeignKeyConstraint(['player_id'], ['player.id'], name=op.f('fk_player_doubles_association_player_id_player')),
    sa.PrimaryKeyConstraint('pair_id', 'player_id', name=op.f('pk_player_doubles_association'))
    )
    op.create_table('team',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('team_nr', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('club_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['club_id'], ['club.id'], name=op.f('fk_team_club_id_club')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_team')),
    sa.UniqueConstraint('name', name=op.f('uq_team_name'))
    )
    op.create_table('matchdate',
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('date_time', sa.DateTime(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.Column('draw_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['draw_id'], ['draw.id'], name=op.f('fk_matchdate_draw_id_draw')),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], name=op.f('fk_matchdate_location_id_location')),
    sa.ForeignKeyConstraint(['season_id'], ['season.id'], name=op.f('fk_matchdate_season_id_season')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_matchdate')),
    sa.UniqueConstraint('url', 'season_id', name=op.f('uq_matchdate_url'))
    )
    op.create_table('pair_teams_association',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('pair_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pair_id'], ['doubles_pair.id'], name=op.f('fk_pair_teams_association_pair_id_doubles_pair')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_pair_teams_association_team_id_team')),
    sa.PrimaryKeyConstraint('team_id', 'pair_id', name=op.f('pk_pair_teams_association'))
    )
    op.create_table('player_teams_association',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['player.id'], name=op.f('fk_player_teams_association_player_id_player')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_player_teams_association_team_id_team')),
    sa.PrimaryKeyConstraint('team_id', 'player_id', name=op.f('pk_player_teams_association'))
    )
    op.create_table('team_draw_assoc',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('draw_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['draw_id'], ['draw.id'], name=op.f('fk_team_draw_assoc_draw_id_draw')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_team_draw_assoc_team_id_team')),
    sa.PrimaryKeyConstraint('team_id', 'draw_id', name=op.f('pk_team_draw_assoc'))
    )
    op.create_table('team_season_assoc',
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('season_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['season_id'], ['season.id'], name=op.f('fk_team_season_assoc_season_id_season')),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], name=op.f('fk_team_season_assoc_team_id_team')),
    sa.PrimaryKeyConstraint('team_id', 'season_id', name=op.f('pk_team_season_assoc'))
    )
    op.create_table('doubles_result',
    sa.Column('match_date_id', sa.Integer(), nullable=False),
    sa.Column('category', sa.Enum('HE1', 'HE2', 'HE3', 'DE1', 'HD1', 'HD2', 'DD1', 'MX1', 'MX2', name='resultcategory'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['match_date_id'], ['matchdate.id'], name=op.f('fk_doubles_result_match_date_id_matchdate')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_doubles_result'))
    )
    op.create_table('match_result',
    sa.Column('match_date_id', sa.Integer(), nullable=False),
    sa.Column('winner', sa.Enum('HOME', 'AWAY', name='winningteam'), nullable=True),
    sa.Column('walkover', sa.Boolean(), nullable=False),
    sa.Column('home_points', sa.Integer(), nullable=False),
    sa.Column('away_points', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['match_date_id'], ['matchdate.id'], name=op.f('fk_match_result_match_date_id_matchdate')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_match_result'))
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
    op.create_table('singles_result',
    sa.Column('match_date_id', sa.Integer(), nullable=False),
    sa.Column('category', sa.Enum('HE1', 'HE2', 'HE3', 'DE1', 'HD1', 'HD2', 'DD1', 'MX1', 'MX2', name='resultcategory'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['match_date_id'], ['matchdate.id'], name=op.f('fk_singles_result_match_date_id_matchdate')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_singles_result'))
    )
    op.create_table('away_pair_result',
    sa.Column('doubles_pair_id', sa.Integer(), nullable=False),
    sa.Column('doubles_result_id', sa.Integer(), nullable=False),
    sa.Column('set_1_points', sa.Integer(), nullable=True),
    sa.Column('set_2_points', sa.Integer(), nullable=True),
    sa.Column('set_3_points', sa.Integer(), nullable=True),
    sa.Column('win', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['doubles_pair_id'], ['doubles_pair.id'], name=op.f('fk_away_pair_result_doubles_pair_id_doubles_pair')),
    sa.ForeignKeyConstraint(['doubles_result_id'], ['doubles_result.id'], name=op.f('fk_away_pair_result_doubles_result_id_doubles_result')),
    sa.PrimaryKeyConstraint('doubles_pair_id', 'doubles_result_id', name=op.f('pk_away_pair_result'))
    )
    op.create_table('away_player_result',
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('singles_result_id', sa.Integer(), nullable=False),
    sa.Column('set_1_points', sa.Integer(), nullable=True),
    sa.Column('set_2_points', sa.Integer(), nullable=True),
    sa.Column('set_3_points', sa.Integer(), nullable=True),
    sa.Column('win', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['player.id'], name=op.f('fk_away_player_result_player_id_player')),
    sa.ForeignKeyConstraint(['singles_result_id'], ['singles_result.id'], name=op.f('fk_away_player_result_singles_result_id_singles_result')),
    sa.PrimaryKeyConstraint('player_id', 'singles_result_id', name=op.f('pk_away_player_result'))
    )
    op.create_table('home_pair_result',
    sa.Column('doubles_pair_id', sa.Integer(), nullable=False),
    sa.Column('doubles_result_id', sa.Integer(), nullable=False),
    sa.Column('set_1_points', sa.Integer(), nullable=True),
    sa.Column('set_2_points', sa.Integer(), nullable=True),
    sa.Column('set_3_points', sa.Integer(), nullable=True),
    sa.Column('win', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['doubles_pair_id'], ['doubles_pair.id'], name=op.f('fk_home_pair_result_doubles_pair_id_doubles_pair')),
    sa.ForeignKeyConstraint(['doubles_result_id'], ['doubles_result.id'], name=op.f('fk_home_pair_result_doubles_result_id_doubles_result')),
    sa.PrimaryKeyConstraint('doubles_pair_id', 'doubles_result_id', name=op.f('pk_home_pair_result'))
    )
    op.create_table('home_player_result',
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('singles_result_id', sa.Integer(), nullable=False),
    sa.Column('set_1_points', sa.Integer(), nullable=True),
    sa.Column('set_2_points', sa.Integer(), nullable=True),
    sa.Column('set_3_points', sa.Integer(), nullable=True),
    sa.Column('win', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['player_id'], ['player.id'], name=op.f('fk_home_player_result_player_id_player')),
    sa.ForeignKeyConstraint(['singles_result_id'], ['singles_result.id'], name=op.f('fk_home_player_result_singles_result_id_singles_result')),
    sa.PrimaryKeyConstraint('player_id', 'singles_result_id', name=op.f('pk_home_player_result'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('home_player_result')
    op.drop_table('home_pair_result')
    op.drop_table('away_player_result')
    op.drop_table('away_pair_result')
    op.drop_table('singles_result')
    op.drop_table('matchdate_home_team_assoc')
    op.drop_table('matchdate_changelog')
    op.drop_table('matchdate_away_team_assoc')
    op.drop_table('match_result')
    op.drop_table('doubles_result')
    op.drop_table('team_season_assoc')
    op.drop_table('team_draw_assoc')
    op.drop_table('player_teams_association')
    op.drop_table('pair_teams_association')
    op.drop_table('matchdate')
    op.drop_table('team')
    op.drop_table('player_doubles_association')
    op.drop_table('draw')
    op.drop_table('club_season_association')
    op.drop_table('season')
    op.drop_table('player')
    op.drop_table('location')
    op.drop_table('doubles_pair')
    op.drop_table('club')
    # ### end Alembic commands ###
