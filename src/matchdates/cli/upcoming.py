import click
import pendulum

from .. import format, models, queries
from . import param_types
from .main import main


def by_date(match_date: models.MatchDate) -> pendulum.DateTime:
    return match_date.date


@main.command("upcoming")
@click.argument("amount", type=int, default=7)
@click.option("--unit", type=click.Choice(["days", "weeks", "months"]), default="days", help="The unit for AMOUNT")
def upcoming(amount, unit):
    """Display a certain AMOUNT of matches in the future"""
    today = pendulum.today().date()
    matches = list(
        models.MatchDate.find(
            queries.match_filter_from_to_day(
                today,
                today + pendulum.duration(**{unit: amount})
            )
    ))
    matches.sort(key=by_date)
    click.echo(
        format.tabulate_match_dates(matches)
    )

