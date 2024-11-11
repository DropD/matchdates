from __future__ import annotations

import re

import pendulum
import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from ..models import MatchDateFromDataResult, MatchDateChangeReason, DocumentFromDataStatus
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

    changelog: Mapped[list[ChangeLogEntry]] = sqla.orm.relationship(
        back_populates="match_date", default_factory=list, repr=False
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


def update_match_date(
    *,
    session: sqla.orm.Session,
    url: str,
    date: str,
    home_team: str,
    away_team: str,
    location: Location,
) -> MatchDateFromDataResult:
    """Find existing match date (update if necessary) or add a new one from upstream."""
    urlmatch = re.match(
        r".*(?P<season_url>league\/.*)\/(?P<match_url>team-match\/\d*).*", url)
    season_url = urlmatch.group("season_url")
    match_url = urlmatch.group("match_url")
    existing = MatchDate.one_or_none(url=match_url)
    session.add(existing)
    session.add(location)
    date_time = pendulum.DateTime.fromisoformat(
        date).astimezone(pendulum.local_timezone())
    if existing:
        change_reasons = []
        if existing.local_date_time != date_time:
            change_reasons.append(MatchDateChangeReason.DATE)
        if existing.location != location:
            change_reasons.append(MatchDateChangeReason.LOCATION)

        if change_reasons:
            if (
                existing.last_change.date_time == existing.date_time
                and existing.last_change.location == existing.location
            ):
                existing.date_time = date_time
                existing.location = location
            else:
                existing.update_with_history(
                    new_date_time=date_time, new_location=location)
            session.commit()
            return MatchDateFromDataResult(
                match_date=existing,
                status=DocumentFromDataStatus.CHANGED,
                change_reasons=change_reasons,
                archive_entry=existing.last_change,
            )
        else:
            return MatchDateFromDataResult(
                match_date=existing, status=DocumentFromDataStatus.UNCHANGED, change_reasons=[]
            )
    else:
        season = Season.one_or_none(url=season_url)
        if not season:
            season = Season(url=season_url)
            session.add(season)
        new = MatchDate(
            url=match_url,
            date_time=date_time,
            home_team=Team.one_or_none(name=home_team),
            away_team=Team.one_or_none(name=away_team),
            location=location,
            season=season,
        )
        session.add(new)
        session.commit()
        return MatchDateFromDataResult(
            match_date=new, status=DocumentFromDataStatus.NEW, change_reasons=[]
        )
