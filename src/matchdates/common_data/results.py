import enum
from typing import Self

import attrs


__all__ = [
    "ResultCategory",
    "Side",
    "Player",
    "Set",
    "SinglesResult",
    "DoublesPair",
    "DoublesResult",
    "TeamMatchResult"
]


class ResultCategory(enum.StrEnum):
    HE1 = enum.auto()
    HE2 = enum.auto()
    HE3 = enum.auto()
    DE1 = enum.auto()
    HD1 = enum.auto()
    HD2 = enum.auto()
    DD1 = enum.auto()
    MX1 = enum.auto()
    MX2 = enum.auto()

    @classmethod
    @property
    def doubles_categories(cls: type[Self]) -> list[Self]:
        return [cls.HD1, cls.HD2, cls.DD1, cls.MX1, cls.MX2]

    @classmethod
    @property
    def singles_categories(cls: type[Self]) -> list[Self]:
        return [cls.HE1, cls.HE2, cls.HE3, cls.DE1]


class Side(enum.StrEnum):
    HOME = enum.auto()
    AWAY = enum.auto()
    NEITHER = enum.auto()
    BOTH = enum.auto()

    @property
    def opposite(self) -> Self:
        cls = self.__class
        match self:
            case cls.HOME:
                return cls.AWAY
            case cls.AWAY:
                return cls.HOME
            case cls.NEITHER:
                return cls.BOTH
            case cls.BOTH:
                return cls.NEITHER
            case _:
                raise ValueError


@attrs.define
class Player:
    name: str
    url: str


@attrs.define
class Set:
    home_points: int
    away_points: int

    @property
    def winner(self) -> Side:
        match self.retired:
            case Side.HOME:
                return Side.AWAY
            case Side.AWAY:
                return Side.HOME
            case _:
                ...

        if self.home_points > self.away_points:
            return Side.HOME
        else:
            return Side.AWAY

    def __str__(self) -> str:
        match self.retired:
            case Side.HOME:
                return f"{self.home_points} (ret.) : {self.away_points}"
            case Side.AWAY:
                return f"{self.home_points} : {self.away_points} (ret.)"
            case _:
                return f"{self.home_points} : {self.away_points}"


@attrs.define
class DoublesPair:
    first: Player
    second: Player

    def __iter__(self):
        yield self.first
        yield self.second


@attrs.define
class SinglesResult:
    home_player: Player | None
    away_player: Player | None
    set_1: Set | None = None
    set_2: Set | None = None
    set_3: Set | None = None
    winner: Side = Side.NEITHER
    retired: Side = Side.NEITHER


@attrs.define
class DoublesResult:
    home_pair: DoublesPair | None
    away_pair: DoublesPair | None
    set_1: Set | None = None
    set_2: Set | None = None
    set_3: Set | None = None
    winner: Side = Side.NEITHER
    retired: Side = Side.NEITHER


@attrs.define
class TeamMatchResult:
    singles: dict[ResultCategory, SinglesResult]
    doubles: dict[ResultCategory, DoublesResult]
    winner: Side
    url: str
