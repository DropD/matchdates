from __future__ import annotations

import typing

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped
from . import base


if typing.TYPE_CHECKING:
    from .matchdate import MatchDate


class Location(base.IDMixin, base.Base):
    """Interclub match venue."""
    __tablename__ = "location"

    name: Mapped[str] = sqla.orm.mapped_column(unique=True)
    address: Mapped[str]
    match_dates: Mapped[list[MatchDate]] = sqla.orm.relationship(
        back_populates="location", init=False)

    def abbrev(self) -> str:
        short_address = "; ".join(self.address.splitlines())[:128]
        return f"{self.name} @ {short_address}"
