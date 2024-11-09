import textwrap

import click
import pendulum
import sqlalchemy as sqla

from . import constants, styling
from .main import main
from .. import queries, format, orm


@main.command("scan")
def scan():
    """Scan for clashes"""
    with sqla.orm.Session(orm.db.get_db()) as session:
        teams = session.query(orm.Team).all()

        for team in sorted(teams, key=lambda t: t.name):
            for clash_result in sorted(
                queries.sqla_match_clashes(
                    team=team, date=pendulum.today()),
                key=lambda clash: clash.day
            ):
                session.add_all(clash_result.matches)
                if not all(
                    match.local_date_time.format("HH:mm") == "00:00"
                    for match in clash_result.matches
                ):
                    click.echo("")
                    click.echo("="*88)
                    click.echo(
                        f"Multiple matches for team {format.color_team(clash_result.team_name)} on the {clash_result.day}:"
                    )
                    click.echo(
                        textwrap.indent(
                            click.style(
                                format.tabulate_match_dates(
                                    clash_result.matches),
                                fg=styling._color_for_severity(
                                    clash_result.severity)
                            ),
                            constants.INDENT
                        )
                    )
