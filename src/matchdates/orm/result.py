from __future__ import annotations

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from . import base
from .player import Player
from .matchdate import MatchDate
from .result_cat import ResultCategory


class SinglesResult(base.IDMixin, base.Base):

    __tablename__ = "singles_result"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(MatchDate.id), init=False, repr=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="singles_results"
    )

    category_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(ResultCategory.id), init=False, repr=False
    )
    category: Mapped[ResultCategory] = sqla.orm.relationship(
        back_populates="results"
    )

    home_player_result: Mapped[HomePlayerResult] = sqla.orm.relationship(
        back_populates="home_singles_result", cascade="all, delete=orphan", init=False, repr=False
    )
    home_player: AssociationProxy[Player] = association_proxy(
        "home_player_result", "player", default=None
    )

    away_player_result: Mapped[AwayPlayerResult] = sqla.orm.relationship(
        back_populates="away_singles_result", cascade="all, delete=orphan", init=False, repr=False
    )
    away_player: AssociationProxy[Player] = association_proxy(
        "away_player_result", "player", default=None
    )


class PlayerResult(base.Base):
    player_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(Player.id), init=False, repr=False, primary_key=True
    )

    singles_result_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(SinglesResult.id), init=False, repr=False, primary_key=True
    )

    set_1_points: Mapped[int | None]
    set_2_points: Mapped[int | None]
    set_3_points: Mapped[int | None]
    win: Mapped[bool | None]

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


class HomePlayerResult(PlayerResult):
    __tablename__ = "home_player_result"

    player: Mapped[Player] = sqla.orm.relationship(
        back_populates="singles_home_player_results"
    )
    singles_result: Mapped[SinglesResult] = sqla.orm.relationship(
        back_populates="home_player_result"
    )


class AwayPlayerResult(PlayerResult):
    __tablename__ = "away_player_result"

    player: Mapped[Player] = sqla.orm.relationship(
        back_populates="singles_away_player_results"
    )
    singles_result: Mapped[SinglesResult] = sqla.orm.relationship(
        back_populates="away_player_result"
    )
