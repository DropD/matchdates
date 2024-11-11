import click
import pendulum
import sqlalchemy as sqla

from .. import format, orm
from .main import main


def by_date(match_date: orm.MatchDate) -> pendulum.DateTime:
    return match_date.date_time


@main.command("upcoming")
@click.argument("amount", type=int, default=7)
@click.option(
    "--unit",
    type=click.Choice(["days", "weeks", "months"]),
    default="days",
    help="The unit for AMOUNT",
)
def upcoming(amount, unit):
    """Display a certain AMOUNT of matches in the future"""
    with orm.db.get_session() as session:
        today = pendulum.today().date()
        matches = session.scalars(orm.MatchDate.select().filter(
            (orm.MatchDate.date_time >= today) &
            (
                orm.MatchDate.date_time <= today +
                pendulum.duration(**{unit: amount})
            )
        )).all()
        matches.sort(key=by_date)
        click.echo(format.tabulate_match_dates(matches))
