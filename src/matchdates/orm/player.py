from __future__ import annotations

import typing
from typing import Self

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped

from . import base, db


class Player(base.IDMixin, base.Base):
    """A Player in the league."""

    __tablename__ = "player"
    url: Mapped[str] = sqla.orm.mapped_column(unique=True, nullable=False)
    name: Mapped[str] = sqla.orm.mapped_column(nullable=False)

    doubles_pairs: Mapped[list[DoublesPair]] = sqla.orm.relationship(
        secondary="player_doubles_association",
        back_populates="players",
        init=False,
        repr=False,
        default_factory=list
    )

    @sqla.orm.validates("doubles_pairs")
    def validate_players(self, key: int, doubles_pair: DoublesPair) -> DoublesPair:
        if len(doubles_pair) > 1:
            raise ValueError(
                f"Doubles pair {doubles_pair} already has two players.")
        elif len(doubles_pair) == 1:
            if existing := DoublesPair.find(self, doubles_pair.players[0]):
                raise ValueError(
                    f"Doubles pair {existing} already exists."
                )
        return doubles_pair

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash((self.url, self.name))


class DoublesPair(base.IDMixin, base.Base):
    """A Doubles or Mixed Doubles Pair."""

    __tablename__ = "doubles_pair"
    players: Mapped[set[Player]] = sqla.orm.relationship(
        secondary="player_doubles_association",
        back_populates="doubles_pairs"
    )  # TODO: this is easy to duplicate?

    def __post_init__(self) -> None:
        if len(self.players) > 2:
            raise ValueError(
                f"Doubles pair can not consist of more than two players!"
            )
        elif len(self.players) == 2:
            if (existing := self.find(*self.players)):
                raise ValueError(f"Doubles pair {existing} already exists")

    @sqla.orm.validates("players")
    def validate_players(self, key: int, player: Player) -> Player:
        if len(self.players) > 1:
            raise ValueError(f"Doubles pair {self} already has two players!")
        elif len(self.players) == 1:
            if (existing := self.find(self.players[0], player)):
                raise ValueError(f"Doubles pair {existing} already exists")
        return player

    def __str__(self) -> str:
        return " / ".join(sorted(p.name for p in self.players))

    def __hash__(self) -> int:
        return hash((str(self)))

    @classmethod
    def find(cls, player_a: Player, player_b: Player) -> Self | None:
        session = db.get_session()
        if player_a.id is None or player_b.id is None:
            return None
        return session.scalars(
            cls.select().filter(
                cls.players.contains(player_a)
                & cls.players.contains(player_b)
            )
        ).one_or_none()

    @classmethod
    def from_players(
        cls: type[Self], player_a: Player, player_b: Player
    ) -> Self:
        """
        Use this to create a new instance or load an existing one.

        Don't forget to add it to the session if is new and should be persisted.
        """
        new = cls.find(player_a, player_b)
        if not new:
            new = cls(players={player_a, player_b})
        return new


class DoublesAssociation(base.Base):

    __tablename__ = "player_doubles_association"
    pair_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(DoublesPair.id), primary_key=True
    )
    player_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(Player.id), primary_key=True
    )
