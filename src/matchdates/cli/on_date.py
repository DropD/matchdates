import click
import pendulum
import sqlalchemy as sqla

from .. import format, models, orm
from . import param_types
from .main import main


def by_date(match_date: models.MatchDate) -> pendulum.DateTime:
    return match_date.date


@main.command("on-date")
@click.argument("day", type=param_types.date.Date())
@click.option("--plusminus", type=int, default=0, help="Show this many days before and after.")
def on_date(day, plusminus):
    """Display matches on DAY"""
    with orm.db.get_session() as session:
        matches = session.scalars(
            orm.MatchDate.select().filter(
                (orm.MatchDate.date_time > day - pendulum.duration(days=plusminus))
                & (orm.MatchDate.date_time < day + pendulum.duration(days=plusminus + 1))
            )
        ).all()
        matches.sort(key=lambda m: m.local_date_time)
        click.echo(format.tabulate_match_dates(matches))
