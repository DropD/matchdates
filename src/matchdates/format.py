import re

import click
import tabulate
import pendulum

from . import models
from . import settings


SETTINGS = settings.SETTINGS["display"]


def shorten_team_name(team_name: str) -> str:
    """
    Shorten team name to fit into a calendar cell.

    Examples:
    >>> short_team_name("BC Zürich Affoltern")
    BCZ-A
    """
    return re.sub(r"[a-ü ]", r"", team_name)


def color_team(team_name: str) -> str:
    """
    Color the team name for CLI output if it is a team from the club of interest.
    """
    if team_name.startswith(SETTINGS["club_name"]):
        return click.style(team_name, bg="blue")
    return team_name


def color_short_team(short_team_name: str) -> str:
    """
    Color the short team name for CLI output if the team is from the club of interest.
    """
    if short_team_name.startswith(shorten_team_name(SETTINGS["club_name"])):
        return click.style(short_team_name, bg="blue")
    return short_team_name


def tabulate_match_dates(matches: list[models.MatchDate]) -> str:
    """
    Format a table for CLI output from a list of match dates.
    """
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
    """
    Format match data to fit within a calendar cell.
    """
    short_home = color_short_team(shorten_team_name(match.home_team))
    short_away = color_short_team(shorten_team_name(match.away_team))
    time = pendulum.instance(match.date).format("HH:mm")
    return f"{short_home} vs {short_away} {time}"
