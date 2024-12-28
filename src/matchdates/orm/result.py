from __future__ import annotations

import enum

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from . import base
from .player import Player
from .matchdate import MatchDate


class ResultCategory(enum.Enum):
    HE1 = "he1"
    HE2 = "he2"
    HE3 = "he3"
    DE1 = "de1"
    HD1 = "hd1"
    DD1 = "dd1"
    MX1 = "mx1"


class SinglesResult(base.IDMixin, base.Base):

    __tablename__ = "singles_result"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(MatchDate.id), init=False, repr=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="singles_results"
    )

    category: Mapped[ResultCategory]

    home_player_result: Mapped[HomePlayerResult] = sqla.orm.relationship(
        back_populates="singles_result", cascade="all, delete-orphan", repr=False
    )
    away_player_result: Mapped[AwayPlayerResult] = sqla.orm.relationship(
        back_populates="singles_result", cascade="all, delete-orphan", repr=False
    )
    home_player: AssociationProxy[Player] = association_proxy(
        "home_player_result", "player", default=None
    )

    away_player: AssociationProxy[Player] = association_proxy(
        "away_player_result", "player", default=None
    )

    def __str__(self) -> str:
        points_str = " ".join([f"{i}:{j}" for i, j in zip(
            self.home_player_result.points, self.away_player_result.points)
            if i is not None or j is not None])
        vs_str = f"{self.home_player.name} vs. {self.away_player.name}"
        return f"{self.category.value.upper()}: {vs_str} - {points_str}"


class PlayerResult(sqla.orm.MappedAsDataclass):

    set_1_points: Mapped[int | None] = sqla.orm.mapped_column(default=None)
    set_2_points: Mapped[int | None] = sqla.orm.mapped_column(default=None)
    set_3_points: Mapped[int | None] = sqla.orm.mapped_column(default=None)
    win: Mapped[bool | None] = sqla.orm.mapped_column(default=None)

    @sqla.orm.validates("set_1_points")
    @sqla.orm.validates("set_2_points")
    @sqla.orm.validates("set_3_points")
    def validate_points(self, key, value):
        if value is None:
            return value
        if value < 0:
            raise ValueError(
                "Points value out of bounds: no negative values allowed.")
        elif value > 30:
            raise ValueError(
                "Points value out of bounds: no values over 30 allowed.")
        return value

    def __post_init__(self):
        self.validate_points("set_1_points", self.set_1_points)
        self.validate_points("set_2_points", self.set_2_points)
        self.validate_points("set_3_points", self.set_3_points)
        if self.set_2_points is None:
            if self.set_3_points is not None:
                raise ValueError(
                    "Can not have points in third set without playing second."
                )
        elif self.set_1_points is None:
            if self.set_2_points is not None:
                raise ValueError(
                    "Can not have points in second set without playing first."
                )

    @property
    def points(self) -> tuple[int | None, int | None, int | None]:
        return (self.set_1_points, self.set_2_points, self.set_3_points)


class HomePlayerResult(PlayerResult, base.Base):
    __tablename__ = "home_player_result"

    player_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(Player.id), init=False, repr=False, primary_key=True
    )

    singles_result_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(SinglesResult.id), init=False, repr=False, primary_key=True
    )

    player: Mapped[Player] = sqla.orm.relationship(
        back_populates="home_singles_results", default=None
    )
    singles_result: Mapped[SinglesResult] = sqla.orm.relationship(
        back_populates="home_player_result", default=None
    )


class AwayPlayerResult(PlayerResult, base.Base):
    __tablename__ = "away_player_result"

    player_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(Player.id), init=False, repr=False, primary_key=True
    )

    singles_result_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(SinglesResult.id), init=False, repr=False, primary_key=True
    )

    player: Mapped[Player] = sqla.orm.relationship(
        back_populates="away_singles_results", default=None
    )
    singles_result: Mapped[SinglesResult] = sqla.orm.relationship(
        back_populates="away_player_result", default=None
    )
