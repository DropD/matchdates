from __future__ import annotations

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy

from matchdates import common_data
from matchdates.orm import base, errors
from matchdates.orm.player import Player
from matchdates.orm.matchdate import MatchDate
from .common import PlayerResultBase


class SinglesResult(base.IDMixin, base.Base):

    __tablename__ = "singles_result"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(MatchDate.id), init=False, repr=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="singles_results"
    )

    category: Mapped[common_data.ResultCategory]

    home_player_result: Mapped[HomePlayerResult] = sqla.orm.relationship(
        back_populates="singles_result", cascade="all, delete-orphan", repr=False,
        default=None
    )
    away_player_result: Mapped[AwayPlayerResult] = sqla.orm.relationship(
        back_populates="singles_result", cascade="all, delete-orphan", repr=False,
        default=None
    )
    home_player: AssociationProxy[Player] = association_proxy(
        "home_player_result", "player", default=None
    )

    away_player: AssociationProxy[Player] = association_proxy(
        "away_player_result", "player", default=None
    )

    def check_completeness(self) -> None:
        if not self.home_player_result or not self.away_player_result:
            raise errors.IncompleteModelError(
                "Can not display points for incomplete SinglesResult.")

    @property
    def points_str(self) -> list[str]:
        self.check_completeness()
        return " ".join(
            [
                f"{i}:{j}" for i, j in zip(
                    self.home_player_result.points,
                    self.away_player_result.points
                )
                if i is not None or j is not None
            ]
        )

    @property
    def table_row(self) -> list:
        self.check_completeness()
        return [
            self.home_player,
            "w" if self.home_player_result.win else "",
            self.away_player,
            "w" if not self.home_player_result.win else "",
            self.points_str
        ]

    def __str__(self) -> str:
        vs_str = f"{self.home_player.name} vs. {self.away_player.name}"
        return f"{self.category.value.upper()}: {vs_str} - {self.points_str}"


class HomePlayerResult(PlayerResultBase, base.Base):
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


class AwayPlayerResult(PlayerResultBase, base.Base):
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
