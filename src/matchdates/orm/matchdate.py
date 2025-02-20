from __future__ import annotations

import typing

import pendulum
import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from . import base
from .location import Location
from .team import Team
from .season import Season
from .draw import Draw


if typing.TYPE_CHECKING:
    from .result import SinglesResult, DoublesResult, MatchResult
    from .player import Player


class MatchDate(base.IDMixin, base.Base):
    """A match date represents the time and place of an interclub match."""

    __tablename__ = "matchdate"
    url: Mapped[str]
    date_time: Mapped[pendulum.DateTime] = sqla.orm.mapped_column(
        sqla.DateTime)

    away_team_assoc: Mapped[AwayTeamAssociation] = sqla.orm.relationship(
        back_populates="match_date", cascade="all, delete-orphan", init=False, repr=False
    )
    away_team: AssociationProxy[Team] = association_proxy(
        "away_team_assoc",
        "team",
        creator=lambda team_obj: AwayTeamAssociation(team=team_obj),
        default=None,
    )

    home_team_assoc: Mapped[HomeTeamAssociation] = sqla.orm.relationship(
        back_populates="match_date", cascade="all, delete-orphan", init=False, repr=False
    )
    home_team: AssociationProxy[Team] = association_proxy(
        "home_team_assoc",
        "team",
        creator=lambda team_obj: HomeTeamAssociation(team=team_obj),
        default=None,
    )

    location_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("location.id"), init=False, repr=False
    )
    location: Mapped[Location] = sqla.orm.relationship(
        back_populates="match_dates", default=None)

    season_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("season.id"), init=False, repr=False
    )
    season: Mapped[Season] = sqla.orm.relationship(
        back_populates="match_dates", default=None)

    draw_id: Mapped[int | None] = sqla.orm.mapped_column(
        sqla.ForeignKey("draw.id"), init=False, repr=False
    )
    draw: Mapped[Draw] = sqla.orm.relationship(
        back_populates="match_dates", default=None
    )

    changelog: Mapped[list[ChangeLogEntry]] = sqla.orm.relationship(
        back_populates="match_date", default_factory=list, repr=False
    )

    singles_results: Mapped[list[SinglesResult]] = sqla.orm.relationship(
        back_populates="match_date", default_factory=list, repr=False
    )

    doubles_results: Mapped[list[DoublesResult]] = sqla.orm.relationship(
        back_populates="match_date", default_factory=list, repr=False
    )

    match_result: Mapped[MatchResult] = sqla.orm.relationship(
        back_populates="match_date", default=None, repr=False
    )

    __table_args__ = (
        sqla.UniqueConstraint("url", "season_id"),
    )

    @property
    def local_date_time(self) -> pendulum.DateTime:
        return pendulum.instance(self.date_time, tz=pendulum.local_timezone())

    @property
    def last_change(self) -> ChangeLogEntry:
        return sorted(self.changelog, key=lambda e: e.archived_date_time)[-1]

    @property
    def full_url(self) -> str:
        return f"https://sb.tournamentsoftware.com/{self.season.url}/{self.url}"

    def update_with_history(self, new_date_time: pendulum.DateTime, new_location: Location) -> None:
        if (new_date_time != self.local_date_time) or (new_location != self.location):
            self.changelog.append(
                ChangeLogEntry(
                    location=self.location,
                    date_time=self.date_time,
                    archived_date_time=pendulum.now(),
                )
            )
            self.date_time = new_date_time
            self.location = new_location

    def __str__(self) -> str:
        return (
            f"{self.home_team} vs {self.away_team} on {self.date_time} at {self.location.name}"
        )

    @property
    def matchnr(self) -> str:
        return self.url.rsplit("/", 1)[1]


class AwayTeamAssociation(base.Base):
    __tablename__ = "matchdate_away_team_assoc"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("matchdate.id"), primary_key=True, init=False
    )
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="away_team_assoc", default=None
    )
    team: Mapped[Team] = sqla.orm.relationship(
        back_populates="away_date_assocs", default=None)


class HomeTeamAssociation(base.Base):
    __tablename__ = "matchdate_home_team_assoc"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("matchdate.id"), primary_key=True, init=False
    )
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="home_team_assoc", default=None
    )
    team: Mapped[Team] = sqla.orm.relationship(
        back_populates="home_date_assocs", default=None)


class ChangeLogEntry(base.Base):
    __tablename__ = "matchdate_changelog"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("matchdate.id"), primary_key=True, init=False
    )
    location_id: Mapped[Location] = sqla.orm.mapped_column(
        sqla.ForeignKey("location.id"), primary_key=True, init=False
    )
    date_time: Mapped[pendulum.DateTime] = sqla.orm.mapped_column(
        sqla.DateTime, primary_key=True)

    archived_date_time: Mapped[pendulum.DateTime] = sqla.orm.mapped_column(
        sqla.DateTime, default_factory=pendulum.now
    )

    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="changelog", default=None)
    location: Mapped[Location] = sqla.orm.relationship(default=None)

    @property
    def local_date_time(self) -> pendulum.DateTime:
        return pendulum.instance(self.date_time, tz=pendulum.local_timezone())


def by_team(team: Team) -> sqla.sql.elements.BooleanClauseList:
    return ((MatchDate.home_team == team) | (MatchDate.away_team == team))


def by_season(season: Season) -> sqla.sql.elements.BinaryExpression:
    return MatchDate.season == season


def player_in_match_for_team(player: Player, match: MatchDate, team: Team) -> bool:
    if match.home_team == team:
        if any(s.home_player == player for s in match.singles_results):
            return True
        elif any(d.home_pair and player in d.home_pair.players for d in match.doubles_results):
            return True
    elif match.away_team == team:
        if any(s.away_player == player for s in match.singles_results):
            return True
        elif any(d.away_pair and player in d.away_pair.players for d in match.doubles_results):
            return True
    return False
