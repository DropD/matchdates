from __future__ import annotations

import typing

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from . import base
from .season import Season


__all__ = ["Club"]


if typing.TYPE_CHECKING:
    from .team import Team


class Club(base.IDMixin, base.Base):
    """A club participating in the interclub league."""

    __tablename__ = "club"
    name: Mapped[str] = sqla.orm.mapped_column(unique=True)
    teams: Mapped[list[Team]] = sqla.orm.relationship(
        back_populates="club", default_factory=list)

    season_assocs: Mapped[list[ClubSeasonAssociation]] = sqla.orm.relationship(
        back_populates="club", cascade="all, delete-orphan", init=False
    )
    seasons: AssociationProxy[list[Season]] = association_proxy(
        "season_assocs",
        "season",
        creator=lambda season_obj: ClubSeasonAssociation(season=season_obj),
        default_factory=list
    )


class ClubSeasonAssociation(base.Base):
    __tablename__ = "club_season_association"
    club_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("club.id"), primary_key=True, init=False
    )
    club: Mapped[Club] = sqla.orm.relationship(
        back_populates="season_assocs", default=None
    )

    season_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("season.id"), primary_key=True, init=False
    )
    season: Mapped[Season] = sqla.orm.relationship(
        back_populates="club_assocs", default=None
    )
#     season_entries: Mapped[list["SeasonClub"]] = sqla.orm.relationship(
#         back_populates="club"
#     )
#
#     @property
#     def seasons(self):
#         return [entry.season for entry in self.season_entries]
#
#
# class SeasonClub(base.Base):
#     "A Club entry in a season."
#
#     __tablename__ = "seasonclub"
#     season_id: Mapped[int] = sqla.orm.mapped_column(
#         sqla.ForeignKey("season.id"))
#     season: Mapped[season_mod.Season] = sqla.orm.relationship(
#         back_populates="club_entries"
#     )
#     club_id: Mapped[int] = sqla.orm.mapped_column(
#         sqla.ForeignKey("club.id"))
#     club: Mapped[Club] = sqla.orm.relationship(
#         back_populates="season_entries"
#     )
