from __future__ import annotations

import enum

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped


class ResultCategory(enum.Enum):
    HE1 = "he1"
    HE2 = "he2"
    HE3 = "he3"
    DE1 = "de1"
    HD1 = "hd1"
    DD1 = "dd1"
    MX1 = "mx1"


class PlayerResultBase(sqla.orm.MappedAsDataclass):

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
