import textwrap

import click
import pendulum

from . import constants, styling
from .main import main
from .. import models, queries, format


@main.command("scan")
def scan():
    """Scan for clashes"""
    teams = set(m.home_team for m in models.MatchDate.find({}))
    teams |= set(m.away_team for m in models.MatchDate.find({}))

    for team in sorted(teams):
        for clash_result in sorted(
            queries.match_same_day_for_team(
                team_name=team, date=pendulum.today()),
            key=lambda clash: clash.day
        ):
            if not all(
                match.date.strftime("%H:%M") == "00:00"
                for match in clash_result.matches
            ):
                click.echo("")
                click.echo("="*88)
                click.echo(
                    f"Multiple matches for team {format.color_team(team)} on the {clash_result.day}:"
                )
                click.echo(
                    textwrap.indent(
                        click.style(
                            format.tabulate_match_dates(clash_result.matches),
                            fg=styling._color_for_severity(
                                clash_result.severity)
                        ),
                        constants.INDENT
                    )
                )
