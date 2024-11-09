from __future__ import annotations

import difflib
import typing

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped

from . import base, db
from ..models import DocumentFromDataStatus, LocationFromDataResult


if typing.TYPE_CHECKING:
    from .matchdate import MatchDate


class Location(base.IDMixin, base.Base):
    """Interclub match venue."""
    __tablename__ = "location"

    name: Mapped[str] = sqla.orm.mapped_column(unique=True)
    address: Mapped[str]
    match_dates: Mapped[list[MatchDate]] = sqla.orm.relationship(
        back_populates="location", init=False, repr=False)

    def abbrev(self) -> str:
        short_address = "; ".join(self.address.splitlines())[:128]
        return f"{self.name} @ {short_address}"


def update_location(name: str, address: str, session: sqla.orm.Session) -> LocationFromDataResult:
    existing = session.query(Location).filter(
        Location.name == name).scalar()
    if existing:
        if existing.address != address:
            diff = difflib.unified_diff(
                existing.address.splitlines(),
                address.splitlines(),
                fromfile="old",
                tofile="new"
            )
            existing.address = address
            session.add(existing)
            session.commit()
            return LocationFromDataResult(
                location=existing,
                status=DocumentFromDataStatus.CHANGED,
                diff=diff
            )
        return LocationFromDataResult(
            location=existing,
            status=DocumentFromDataStatus.UNCHANGED,
            diff=[]
        )
    else:
        new = Location(name=name, address=address)
        session.add(new)
        session.commit()
        return LocationFromDataResult(
            location=new,
            status=DocumentFromDataStatus.NEW,
            diff=[]
        )
