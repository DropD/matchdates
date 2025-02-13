from __future__ import annotations

import enum
import tabulate
import textwrap

import sqlalchemy as sqla
from sqlalchemy.orm import Mapped

from matchdates.orm import base
from matchdates.orm.matchdate import MatchDate
from matchdates import common_data


class WinningTeam(enum.Enum):
    HOME = "home"
    AWAY = "away"


def cat_order() -> list[common_data.ResultCategory]:
    return [
        common_data.ResultCategory.HE1,
        common_data.ResultCategory.HE2,
        common_data.ResultCategory.HE3,
        common_data.ResultCategory.DE1,
        common_data.ResultCategory.HD1,
        common_data.ResultCategory.HD2,
        common_data.ResultCategory.DD1,
        common_data.ResultCategory.MX1,
        common_data.ResultCategory.MX2
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
