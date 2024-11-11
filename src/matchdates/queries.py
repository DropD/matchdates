import dataclasses
import enum
import itertools
from typing import Any, Iterator

import pendulum
import sqlalchemy as sqla

from . import date_utils
from . import orm


def match_filter_by_team(team_name: str) -> dict[str, dict[str, str]]:
    return {
        "$or": [
            {"home_team": team_name},
            {"away_team": team_name},
        ],
    }


def match_group_by_match_day() -> dict[str, dict[str, Any]]:
    return {
        "$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": "$date",
                },
            },
            "count": {"$sum": 1},
            "matches": {"$addToSet": "$url"},
        }
    }


def match_filter_around_day(day: pendulum.Date, plusminus: int = 0) -> dict[str, Any]:
    return match_filter_from_to_day(
        start=day - pendulum.duration(days=plusminus),
        end=day + pendulum.duration(days=plusminus + 1),
    )


def match_filter_from_to_day(start: pendulum.Date, end: pendulum.Date) -> dict[str, Any]:
    return {
        "date": {"$gt": date_utils.date_to_datetime(start), "$lt": date_utils.date_to_datetime(end)}
    }


def match_list_field_values(field_name: str) -> dict[str, Any]:
    return {"$group": {"_id": None, "teams": {"$addToSet": f"${field_name}"}}}


class MatchClashSeverity(enum.IntEnum):
    UNPLAYABLE = 100
    WARNING = 10
    PROBABLY_INTENTIONAL = 1


@dataclasses.dataclass(frozen=True, kw_only=True)
class MatchClashResult:
    day: pendulum.Date
    team_name: str
    matches: list[orm.MatchDate]

    @property
    def severity(self):
        combinations = itertools.combinations(
            [pendulum.instance(m.date_time) for m in self.matches], 2
        )
        time_between = [abs(c[0] - c[1]).total_hours() for c in combinations]
        # not enough time in between matches
        if any([dt < 2.25 for dt in time_between]):
            return MatchClashSeverity.UNPLAYABLE
        # multiple locations on same day but potentially enough time if they are close
        elif len(set(m.location.id for m in self.matches)) > 1:
            # not enough time in the general case
            if any([dt < 3.75 for dt in time_between]):
                return MatchClashSeverity.UNPLAYABLE
            return MatchClashSeverity.WARNING
        # if we get to here it's in the same place with enough time
        return MatchClashSeverity.PROBABLY_INTENTIONAL


def sqla_match_clashes(team: orm.Team, date=pendulum.Date) -> Iterator[MatchClashResult]:
    with orm.db.get_session() as session:
        groups = list(
            session.execute(
                sqla.select(
                    sqla.func.strftime("%Y-%m-%d", orm.MatchDate.date_time),
                    sqla.func.aggregate_strings(orm.MatchDate.id, ", "),
                )
                .filter(
                    ((orm.MatchDate.home_team == team) |
                     (orm.MatchDate.away_team == team))
                    & (orm.MatchDate.date_time > date_utils.season_start(date).naive())
                    & (orm.MatchDate.date_time <= date_utils.season_end(date).naive())
                )
                .group_by(sqla.func.strftime("%Y-%m-%d", orm.MatchDate.date_time))
                .having(sqla.func.count() > 1)
            )
        )
        for date_str, match_ids in groups:
            yield MatchClashResult(
                day=pendulum.from_format(date_str, "YYYY-MM-DD"),
                team_name=team.name,
                matches=[session.get(orm.MatchDate, int(id))
                         for id in match_ids.split(", ")],
            )
