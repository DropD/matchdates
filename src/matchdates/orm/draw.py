from __future__ import annotations

import typing

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy


from . import base
from . season import Season


__all__ = ["Draw"]


if typing.TYPE_CHECKING:
    from .team import Team, TeamDrawAssociation
    from .matchdate import MatchDate


class Draw(base.IDMixin, base.Base):
    """An interclub group."""

    __tablename__ = "draw"
    url: Mapped[str]

    season_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey("season.id"), init=False, repr=False)

    season: Mapped[Season] = sqla.orm.relationship(
        back_populates="draws", default=None)

    team_assocs: Mapped[list[TeamDrawAssociation]] = sqla.orm.relationship(
        back_populates="draw",
        cascade="all, delete-orphan",
        init=False,
        repr=False
    )
    teams: AssociationProxy[list[Team]] = association_proxy(
        "team_assocs",
        "team",
        creator=lambda team_obj: TeamDrawAssociation(team=team_obj),
        default_factory=list,
        repr=False,
    )

    match_dates: Mapped[list[MatchDate]] = sqla.orm.relationship(
        back_populates="draw", default_factory=list, repr=False
    )

    __table_args__ = (
        sqla.UniqueConstraint("url", "season_id"),
    )
