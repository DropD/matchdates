import tabulate
import pendulum

from . import models


def tabulate_match_dates(matches: list[models.MatchDate]) -> str:
    headers = ["Weekday", "Date", "Time", "Home Team", "Away Team", "Nr", "Location"]
    return tabulate.tabulate(
        [
            (
                (d := pendulum.instance(m.date)).format("dd"),
                m.date.date().isoformat(),
                d.format("HH:mm"),
                m.home_team,
                m.away_team,
                m.url.rsplit("/", 1)[-1],
                m.location.fetch().name
            ) for m in matches
        ],
        headers=headers
    )

