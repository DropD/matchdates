from __future__ import annotations

import typing

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy


from . import base
from .season import Season
from .club import Club


__all__ = ["Team"]


if typing.TYPE_CHECKING:
    from .matchdate import MatchDate, AwayTeamAssociation, HomeTeamAssociation


def create_away_team_assoc(match_date_obj: MatchDate) -> AwayTeamAssociation:
    from .matchdate import AwayTeamAssociation
    return AwayTeamAssociation(match_date=match_date_obj)


def create_home_team_assoc(match_date_obj: MatchDate) -> HomeTeamAssociation:
    from .matchdate import HomeTeamAssociation
    return HomeTeamAssociation(match_date=match_date_obj)


class Team(base.IDMixin, base.Base):
    """A team in the league."""

    __tablename__ = "team"
    name: Mapped[str] = sqla.orm.mapped_column(unique=True)
    team_nr: Mapped[int] = sqla.orm.mapped_column(unique=True)

    club_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("club.id"), init=False)
    club: Mapped[Club] = sqla.orm.relationship(back_populates="teams")

    season_assocs: Mapped[list[TeamSeasonAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False
    )
    seasons: AssociationProxy[list[Season]] = association_proxy(
        "season_assocs",
        "season",
        creator=lambda season_obj: TeamSeasonAssociation(season=season_obj),
        default_factory=list
    )

    away_date_assocs: Mapped[list[AwayTeamAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False
    )
    away_dates: AssociationProxy[list[MatchDate]] = association_proxy(
        "away_date_assocs",
        "match_date",
        creator=create_away_team_assoc,
        default_factory=list
    )

    home_date_assocs: Mapped[list[HomeTeamAssociation]] = sqla.orm.relationship(
        back_populates="team", cascade="all, delete-orphan", init=False
    )
    home_dates: AssociationProxy[list[MatchDate]] = association_proxy(
        "home_date_assocs",
        "match_date",
        creator=create_home_team_assoc,
        default_factory=list,
    )


class TeamSeasonAssociation(base.Base):
    __tablename__ = "team_season_assoc"
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False
    )
    season_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("season.id"), primary_key=True, init=False
    )
    team: Mapped[Team] = sqla.orm.relationship(
        back_populates="season_assocs", default=None
    )
    season: Mapped[Season] = sqla.orm.relationship(
        back_populates="team_assocs", default=None
    )


# @property
# def seasons(self):
#     return [entry.season for entry in self.season_entries]

# class SeasonTeam(base.Base):
#     """A Team entry in a season."""
#
#     __tablename__ = "seasonteam"
#     id: Mapped[int] = sqla.orm.mapped_column(init=False, primary_key=True)
#     season_id: Mapped[int] = sqla.orm.mapped_column(
#         sqla.ForeignKey("season.id"))
#     season: Mapped[Season] = sqla.orm.relationship(
#         back_populates="team_entries")
#     team_id: Mapped[int] = sqla.orm.mapped_column(
#         sqla.ForeignKey("team.id"))
#     team: Mapped[Team] = sqla.orm.relationship(
#         back_populates="season_entries")
