from __future__ import annotations

import enum
import tabulate
import textwrap

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped

from matchdates.orm import base
from matchdates.orm.matchdate import MatchDate
from .common import ResultCategory


class WinningTeam(enum.Enum):
    HOME = "home"
    AWAY = "away"


def cat_order() -> list[ResultCategory]:
    return [
        ResultCategory.HE1,
        ResultCategory.HE2,
        ResultCategory.HE3,
        ResultCategory.DE1,
        ResultCategory.HD1,
        ResultCategory.DD1,
        ResultCategory.MX1
    ]


class MatchResult(base.IDMixin, base.Base):

    __tablename__ = "match_result"
    match_date_id: Mapped[int] = sqla.orm.mapped_column(
        sqla.ForeignKey(MatchDate.id), init=False, repr=False
    )
    match_date: Mapped[MatchDate] = sqla.orm.relationship(
        back_populates="match_result"
    )
    winner: Mapped[WinningTeam | None]
    walkover: Mapped[bool]
    home_points: Mapped[int]
    away_points: Mapped[int]

    def render(self) -> str:
        results = sorted(
            self.match_date.singles_results + self.match_date.doubles_results,
            key=lambda r: cat_order().index(r.category)
        )
        results_str = tabulate.tabulate(
            [[res.category.value.upper()] + res.table_row for res in results])
        return f"{self.match_date}\npoints {self.home_points} : {self.away_points}\n{textwrap.indent(results_str, prefix=' '*2)}"
