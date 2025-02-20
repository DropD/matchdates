from __future__ import annotations

import typing

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy


from . import base
from .season import Season
from .draw import Draw
from .club import Club


__all__ = ["Team"]


if typing.TYPE_CHECKING:
    from .matchdate import MatchDate, AwayTeamAssociation, HomeTeamAssociation
    from .player import DoublesPair, Player, TeamAssociation, TeamPairAssociation


def create_away_team_assoc(match_date_obj: MatchDate) -> AwayTeamAssociation:
    from .matchdate import AwayTeamAssociation

    return AwayTeamAssociation(match_date=match_date_obj)


def create_home_team_assoc(match_date_obj: MatchDate) -> HomeTeamAssociation:
    from .matchdate import HomeTeamAssociation

    return HomeTeamAssociation(match_date=match_date_obj)


def create_player_team_assoc(player_obj: Player) -> TeamAssociation:
    from .player import TeamAssociation

    return TeamAssociation(player=player_obj)


def create_pair_team_assoc(pair_obj: DoublesPair) -> TeamPairAssociation:
    from .player import TeamPairAssociation
    return TeamPairAssociation(pair=pair_obj)


class Team(base.IDMixin, base.Base):
    """A team in the league."""

    __tablename__ = "team"
    name: Mapped[str] = sqla.orm.mapped_column(unique=True)
    team_nr: Mapped[int] = sqla.orm.mapped_column(unique=False)
    url: Mapped[str | None]

    club_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("club.id"), init=False, repr=False
    )
    club: Mapped[Club] = sqla.orm.relationship(back_populates="teams")

    season_assocs: Mapped[list[TeamSeasonAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False, repr=False
    )
    seasons: AssociationProxy[list[Season]] = association_proxy(
        "season_assocs",
        "season",
        creator=lambda season_obj: TeamSeasonAssociation(season=season_obj),
        default_factory=list,
        repr=False,
    )

    draw_assocs: Mapped[list[TeamDrawAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False, repr=False
    )
    draws: AssociationProxy[list[Draw]] = association_proxy(
        "draw_assocs",
        "draw",
        init=False,
        creator=lambda draw_obj: TeamDrawAssociation(draw=draw_obj),
        default_factory=list,
        repr=False,
    )

    away_date_assocs: Mapped[list[AwayTeamAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False, repr=False
    )
    away_dates: AssociationProxy[list[MatchDate]] = association_proxy(
        "away_date_assocs",
        "match_date",
        creator=create_away_team_assoc,
        default_factory=list,
        repr=False,
    )

    home_date_assocs: Mapped[list[HomeTeamAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False, repr=False
    )
    home_dates: AssociationProxy[list[MatchDate]] = association_proxy(
        "home_date_assocs",
        "match_date",
        creator=create_home_team_assoc,
        default_factory=list,
        repr=False,
    )

    player_assocs: Mapped[list[TeamAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False, repr=False
    )
    players: AssociationProxy[list[Player]] = association_proxy(
        "player_assocs",
        "player",
        creator=create_player_team_assoc,
        default_factory=list, repr=False
    )

    pair_assocs: Mapped[list[TeamPairAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False, repr=False
    )
    doubles_pairs: AssociationProxy[list[DoublesPair]] = association_proxy(
        "pair_assocs",
        "pair",
        creator=create_pair_team_assoc,
        default_factory=list, repr=False
    )

    def __str__(self):
        return self.name


class TeamSeasonAssociation(base.Base):
    __tablename__ = "team_season_assoc"
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False
    )
    season_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("season.id"), primary_key=True, init=False
    )
    team: Mapped[Team] = sqla.orm.relationship(
        back_populates="season_assocs", default=None)
    season: Mapped[Season] = sqla.orm.relationship(
        back_populates="team_assocs", default=None)


class TeamDrawAssociation(base.Base):
    __tablename__ = "team_draw_assoc"
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False
    )
    draw_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("draw.id"), primary_key=True, init=False
    )
    team: Mapped[Team] = sqla.orm.relationship(
        back_populates="draw_assocs", default=None)
    draw: Mapped[Draw] = sqla.orm.relationship(
        back_populates="team_assocs", default=None)
