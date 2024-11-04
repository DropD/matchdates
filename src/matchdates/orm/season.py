from __future__ import annotations

import typing

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


class Season(base.IDMixin, base.Base):
    """A Season of interclub."""

    __tablename__ = "season"
    url: Mapped[str] = sqla.orm.mapped_column(unique=True)

    team_assocs: Mapped[list[TeamSeasonAssociation]] = sqla.orm.relationship(
        back_populates="season", cascade="all, delete-orphan", init=False
    )
    teams: AssociationProxy[list[Team]] = association_proxy(
        "team_assocs",
        "team",
        creator=lambda team_obj: TeamSeasonAssociation(team=team_obj),
        default_factory=list
    )

    club_assocs: Mapped[list[ClubSeasonAssociation]] = sqla.orm.relationship(
        back_populates="season", cascade="all, delete-orphan", init=False
    )
    clubs: AssociationProxy[list[Club]] = association_proxy(
        "club_assocs",
        "club",
        creator=lambda club_obj: ClubSeasonAssociation(club=club_obj),
        default_factory=list
    )

    match_dates: Mapped[list[MatchDate]] = sqla.orm.relationship(
        back_populates="season", default_factory=list
    )
    # club_entries: Mapped[list["SeasonClub"]] = sqla.orm.relationship(
    #     back_populates="season"
    # )
    #
    # @property
    # def clubs(self):
    #     return [entry.club for entry in self.club_entries]
