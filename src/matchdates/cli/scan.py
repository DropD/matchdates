import textwrap

import click

from . import constants, styling
from .main import main
from .. import models, queries, format


@main.command("scan")
def scan():
    """Scan for clashes"""
    teams = set(m.home_team for m in models.MatchDate.find({}))
    teams |= set(m.away_team for m in models.MatchDate.find({}))

    for team in teams:
        for clash_result in queries.match_same_day_for_team(team_name=team):
            click.echo(f"Multiple matches for team {team} on the {clash_result.day}:")
            click.echo(
                textwrap.indent(
                    click.style(
                        format.tabulate_match_dates(clash_result.matches),
                        fg=styling._color_for_severity(clash_result.severity)
                    ),
                    constants.INDENT
                )
            )

