from __future__ import annotations

import typing
from typing import Self

import pendulum
import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy


from . import base


__all__ = ["Season"]


if typing.TYPE_CHECKING:
    from .team import Team, TeamSeasonAssociation
    from .club import Club, ClubSeasonAssociation
    from .matchdate import MatchDate
    from .draw import Draw


class Season(base.IDMixin, base.Base):
    """A Season of interclub."""

    __tablename__ = "season"
    url: Mapped[str] = sqla.orm.mapped_column(unique=True)
    name: Mapped[str]
    start_date: Mapped[pendulum.Date] = sqla.orm.mapped_column(
        sqla.Date)
    end_date: Mapped[pendulum.Date] = sqla.orm.mapped_column(
        sqla.Date)

    team_assocs: Mapped[list[TeamSeasonAssociation]] = sqla.orm.relationship(
        back_populates="season", cascade="all, delete-orphan", init=False, repr=False
    )
    teams: AssociationProxy[list[Team]] = association_proxy(
        "team_assocs",
        "team",
        creator=lambda team_obj: TeamSeasonAssociation(team=team_obj),
        default_factory=list,
        repr=False,
    )

    club_assocs: Mapped[list[ClubSeasonAssociation]] = sqla.orm.relationship(
        back_populates="season", cascade="all, delete-orphan", init=False, repr=False
    )
    clubs: AssociationProxy[list[Club]] = association_proxy(
        "club_assocs",
        "club",
        creator=lambda club_obj: ClubSeasonAssociation(club=club_obj),
        default_factory=list,
        repr=False,
    )

    match_dates: Mapped[list[MatchDate]] = sqla.orm.relationship(
        back_populates="season", default_factory=list, repr=False
    )

    draws: Mapped[list[Draw]] = sqla.orm.relationship(
        back_populates="season", default_factory=list, repr=False
    )
    # club_entries: Mapped[list["SeasonClub"]] = sqla.orm.relationship(
    #     back_populates="season"
    # )
    #
    # @property
    # def clubs(self):
    #     return [entry.club for entry in self.club_entries]

    @classmethod
    def current(cls) -> Self:
        return next(iter(sorted(cls.all(), key=lambda s: s.end_date, reverse=True)))

    def __str__(self) -> str:
        return self.name
