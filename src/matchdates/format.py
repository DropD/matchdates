import re

import click
import tabulate
import pendulum

from . import orm
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


def tabulate_match_dates(matches: list[orm.MatchDate]) -> str:
    """
    Format a table for CLI output from a list of match dates.
    """
    headers = ["Weekday", "Date", "Time",
               "Home Team", "Away Team", "Nr", "Location"]
    return tabulate.tabulate(
        [
            (
                (d := pendulum.instance(m.local_date_time)).format("dd"),
                d.date().isoformat(),
                d.format("HH:mm"),
                color_team(m.home_team.name),
                color_team(m.away_team.name),
                m.url.rsplit("/", 1)[-1],
                m.location.name,
            )
            for m in matches
        ],
        headers=headers,
    )


def tabulate_match_results(results: list[orm.MatchResult]) -> str:
    """
    Format a table for CLI output from a list of match results.
    """
    headers = [
        "Weekday", "Date", "Home Team",
        "", "", "", "Away Team", "URL"
    ]
    return tabulate.tabulate(
        [
            (
                (d := pendulum.instance(r.match_date.local_date_time)).format("dd"),
                d.date().isoformat(),
                color_team(r.match_date.home_team.name),
                r.home_points,
                ":",
                r.away_points,
                color_team(r.match_date.away_team.name),
                r.match_date.full_url,
            )
            for r in results
        ],
        headers=headers
    )


def short_form_match(match: orm.MatchDate) -> str:
    """
    Format match data to fit within a calendar cell.
    """
    short_home = color_short_team(shorten_team_name(match.home_team.name))
    short_away = color_short_team(shorten_team_name(match.away_team.name))
    time = match.local_date_time.format("HH:mm")
    return f"{short_home} vs {short_away} {time}"
