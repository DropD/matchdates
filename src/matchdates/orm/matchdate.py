from __future__ import annotations

import pendulum
import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from . import base
from .location import Location
from .team import Team
from .season import Season


class MatchDate(base.IDMixin, base.Base):
    """A match date represents the time and place of an interclub match."""

    __tablename__ = "matchdate"
    url: Mapped[str] = sqla.orm.mapped_column(unique=True)
    date_time: Mapped[pendulum.DateTime] = sqla.orm.mapped_column(
        sqla.DateTime)

    away_team_assoc: Mapped[AwayTeamAssociation] = sqla.orm.relationship(
        back_populates="match_date", cascade="all, delete-orphan", init=False
    )
    away_team: AssociationProxy[Team] = association_proxy(
        "away_team_assoc",
        "team",
        creator=lambda team_obj: AwayTeamAssociation(team=team_obj),
        default=None
    )

    home_team_assoc: Mapped[HomeTeamAssociation] = sqla.orm.relationship(
        back_populates="match_date", cascade="all, delete-orphan", init=False
    )
    home_team: AssociationProxy[Team] = association_proxy(
        "home_team_assoc",
        "team",
        creator=lambda team_obj: HomeTeamAssociation(team=team_obj),
        default=None
    )

    location_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("location.id"), init=False)
    location: Mapped[Location] = sqla.orm.relationship(
        back_populates="match_dates", default=None)

    season_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("season.id"), init=False
    )
    season: Mapped[Season] = sqla.orm.relationship(
        back_populates="match_dates", default=None
    )

    changelog: Mapped[list[ChangeLogEntry]] = sqla.orm.relationship(
        back_populates="match_date", default_factory=list
    )

    @property
    def local_date_time(self) -> pendulum.DateTime:
        return pendulum.instance(self.date_time, tz=pendulum.local_timezone())

    def update_with_history(
        self, new_date_time: pendulum.DateTime, new_location: Location
    ) -> None:
        if (
            (new_date_time != self.local_date_time)
            or (new_location != self.location)
        ):
            self.changelog.append(
                ChangeLogEntry(
                    location=self.location, date_time=self.date_time
                )
            )
            self.date_time = new_date_time
            self.location = new_location


class AwayTeamAssociation(base.Base):
    __tablename__ = "matchdate_away_team_assoc"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("matchdate.id"), primary_key=True, init=False)
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False)
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="away_team_assoc", default=None)
    team: Mapped[Team] = sqla.orm.relationship(
        back_populates="away_date_assocs", default=None)


class HomeTeamAssociation(base.Base):
    __tablename__ = "matchdate_home_team_assoc"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("matchdate.id"), primary_key=True, init=False)
    team_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("team.id"), primary_key=True, init=False)
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="home_team_assoc", default=None)
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
        back_populates="changelog", default=None
    )
    location: Mapped[Location] = sqla.orm.relationship(default=None)

    @property
    def local_date_time(self) -> pendulum.DateTime:
        return pendulum.instance(self.date_time, tz=pendulum.local_timezone())
