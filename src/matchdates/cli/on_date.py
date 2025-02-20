import click
import pendulum

from .. import format, orm
from . import param_types
from .main import main


@main.command("on-date")
@click.argument("day", type=param_types.date.Date())
@click.option("--plusminus", type=int, default=0, help="Show this many days before and after.")
def on_date(day, plusminus):
    """Display matches on DAY"""
    matches = orm.MatchDate.filter(
        (orm.MatchDate.date_time > day - pendulum.duration(days=plusminus))
        & (orm.MatchDate.date_time < day + pendulum.duration(days=plusminus + 1))
    )
    matches.sort(key=lambda m: m.local_date_time)
    click.echo(format.tabulate_match_dates(matches))
