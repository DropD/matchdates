import re

import click
import tabulate
import pendulum

from . import models


def color_team(team_name: str) -> str:
    if team_name.startswith("BC Zürich-Affoltern"):
        return click.style(team_name, bg="blue")
    return team_name


def color_short_team(short_team_name: str) -> str:
    if short_team_name.startswith("BCZ-A"):
        return click.style(short_team_name, bg="blue")
    return short_team_name


def tabulate_match_dates(matches: list[models.MatchDate]) -> str:
    headers = ["Weekday", "Date", "Time", "Home Team", "Away Team", "Nr", "Location"]
    return tabulate.tabulate(
        [
            (
                (d := pendulum.instance(m.date)).format("dd"),
                m.date.date().isoformat(),
                d.format("HH:mm"),
                color_team(m.home_team),
                color_team(m.away_team),
                m.url.rsplit("/", 1)[-1],
                m.location.fetch().name
            ) for m in matches
        ],
        headers=headers
    )

def short_form_match(match: models.MatchDate) -> str:
    short_home = color_short_team(re.sub(r"[a-ü ]", r"", match.home_team))
    short_away = color_short_team(re.sub(r"[a-ü ]", r"", match.away_team))
    time = pendulum.instance(match.date).format("HH:mm")
    return f"{short_home} vs {short_away} {time}"
