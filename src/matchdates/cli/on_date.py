import click
import pendulum

from .. import format, models, queries
from . import param_types
from .main import main


def by_date(match_date: models.MatchDate) -> pendulum.DateTime:
    return match_date.date


@main.command("on-date")
@click.argument("day", type=param_types.date.Date())
@click.option("--plusminus", type=int, default=0, help="Show this many days before and after.")
def on_date(day, plusminus):
    """Display matches on DAY"""
    matches = list(
        models.MatchDate.find(
            queries.match_filter_around_day(day, plusminus)
    ))
    matches.sort(key=by_date)
    click.echo(
        format.tabulate_match_dates(matches)
    )
