from __future__ import annotations

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from matchdates.orm import base
from matchdates.orm.player import DoublesPair
from matchdates.orm.matchdate import MatchDate
from .common import ResultCategory, PlayerResultBase


class DoublesResult(base.IDMixin, base.Base):

    __tablename__ = "doubles_result"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(MatchDate.id), init=False, repr=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="doubles_results"
    )

    category: Mapped[ResultCategory]

    home_pair_result: Mapped[HomePairResult] = sqla.orm.relationship(
        back_populates="doubles_result", cascade="all, delete-orphan",
        repr=False
    )
    away_pair_result: Mapped[AwayPairResult] = sqla.orm.relationship(
        back_populates="doubles_result", cascade="all, delete-orphan",
        repr=False
    )

    home_pair: AssociationProxy[DoublesPair] = association_proxy(
        "home_pair_result", "doubles_pair", default=None
    )
    away_pair: AssociationProxy[DoublesPair] = association_proxy(
        "away_pair_result", "doubles_pair", default=None
    )

    def __str__(self) -> str:
        points_str = " ".join(
            [
                f"{i}:{j}" for i, j in zip(
                    self.home_pair_result.points,
                    self.away_pair_result.points
                ) if i is not None or j is not None
            ]
        )
        vs_str = f"{self.home_pair} vs. {self.away_pair}"
        return f"{self.category.value.upper()}: {vs_str} - {points_str}"


class HomePairResult(PlayerResultBase, base.Base):
    __tablename__ = "home_pair_result"

    doubles_pair_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(DoublesPair.id), init=False, repr=False,
        primary_key=True
    )
    doubles_result_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(DoublesResult.id), init=False, repr=False,
        primary_key=True
    )

    doubles_pair: Mapped[DoublesPair] = sqla.orm.relationship(
        back_populates="home_doubles_results", default=None
    )
    doubles_result: Mapped[DoublesResult] = sqla.orm.relationship(
        back_populates="home_pair_result", default=None
    )


class AwayPairResult(PlayerResultBase, base.Base):
    __tablename__ = "away_pair_result"

    doubles_pair_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(DoublesPair.id), init=False, repr=False,
        primary_key=True
    )
    doubles_result_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(DoublesResult.id), init=False, repr=False,
        primary_key=True
    )

    doubles_pair: Mapped[DoublesPair] = sqla.orm.relationship(
        back_populates="away_doubles_results", default=None
    )
    doubles_result: Mapped[DoublesResult] = sqla.orm.relationship(
        back_populates="away_pair_result", default=None
    )
