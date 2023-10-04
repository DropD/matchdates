import dataclasses
import enum
import itertools
from typing import Any, Iterator
from typing_extensions import Self

import pendulum

from . import models
from . import date_utils


def match_filter_by_team(team_name: str) -> dict[str, dict[str, str]]:
    return {
        "$or": [
            {"home_team": team_name},
            {"away_team": team_name},
        ],
    }


def match_group_by_mach_day() -> dict[str, dict[str, Any]]:
    return {
        "$group": {
            "_id": {
                "$dateToString": {
                    "format": "%Y-%m-%d", "date": "$date",
                },
            },
            "count": {"$sum": 1},
            "matches": {"$addToSet": "$url"}
        }
    }


def match_filter_around_day(day: pendulum.Date, plusminus: int = 0) -> dict[str, Any]:
    return match_filter_from_to_day(
        start=day - pendulum.duration(days=plusminus),
        end=day + pendulum.duration(days=plusminus + 1)
    )


def match_filter_from_to_day(start: pendulum.Date, end: pendulum.Date) -> dict[str, Any]:
    return {
        "date": {
            "$gt": date_utils.date_to_datetime(start),
            "$lt": date_utils.date_to_datetime(end)
        }
    }


def match_list_field_values(field_name: str) -> dict[str, Any]:
    return {
        "$group": {
            "_id": None,
            "teams": {"$addToSet": f"${field_name}"}
        }
    }


class MatchClashSeverity(enum.IntEnum):
    UNPLAYABLE = 100
    WARNING = 10
    PROBABLY_INTENTIONAL = 1


@dataclasses.dataclass(frozen=True, kw_only=True)
class MatchClashResult:
    day: pendulum.Date
    team_name: str
    matches: list[models.MatchDate]

    @property
    def severity(self):
        combinations = itertools.combinations(
            [pendulum.instance(m.date) for m in self.matches],
            2
        )
        time_between = [abs(c[0] - c[1]).total_hours() for c in combinations]
        # not enough time in between matches
        if any([dt < 2.25 for dt in time_between]):
            return MatchClashSeverity.UNPLAYABLE
        # multiple locations on same day but potentially enough time if they are close
        elif len(set(m.location.fetch().id for m in self.matches)) > 1:
            # not enough time in the general case
            if any([dt < 3.75 for dt in time_between]):
                return MatchClashSeverity.UNPLAYABLE
            return MatchClashSeverity.WARNING
        # if we get to here it's in the same place with enough time
        return MatchClashSeverity.PROBABLY_INTENTIONAL

    @classmethod
    def from_query_item(
            cls: type[Self],
            *,
            team_name: str,
            _id: str,
            count: int,
            matches: list[str]
        ) -> Self:
        assert count > 1, "Trying to build a MatchClashResult from not a clash"
        return cls(
            day=pendulum.Date.fromisoformat(_id),
            team_name=team_name,
            matches=list(models.MatchDate.find({"url": {"$in": matches}}))
        )



def match_same_day_for_team(team_name: str) -> Iterator[MatchClashResult]:
    query = models.MatchDate.collection.aggregate([
        {"$match": match_filter_by_team(team_name)},
        match_group_by_mach_day(),
        {"$match": {"count": {"$gt": 1}}}
    ])
    for item in query:
        yield MatchClashResult.from_query_item(team_name=team_name, **item)
