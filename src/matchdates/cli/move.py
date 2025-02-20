import click
import copy
import pendulum
import tabulate
from typing import Optional

import sqlalchemy as sqla

from .. import format, orm
from . import calendar, param_types
from .main import main


@main.command("move")
@click.argument("match", type=param_types.match.Match())
@click.option("--date", type=param_types.date.Date())
@click.option("--time", type=str)
def move(match: orm.MatchDate, date: Optional[pendulum.Date], time: Optional[str]) -> None:
    """
    Pretend to move a match and show the new and old date in calendar context.

    Does not actually move anything. Does not modify the local database.
    Definitely does not do anything on the Swiss-Badminton system.
    """
    with orm.db.get_session() as session:
        time = time or match.local_date_time.format("HH:mm")
        date = date or match.local_date_time.date()
        moved = copy.copy(match)
        moved.date_time = pendulum.DateTime.fromisoformat(
            f"{date.isoformat()} {time}")
        cal = calendar.Month(first=moved.local_date_time.start_of("month"))
        matches = session.scalars(
            orm.MatchDate.select().filter(
                (orm.MatchDate.date_time >= cal.first) & (
                    orm.MatchDate.date_time <= cal.last)
            )
        )
        for existing_match in matches:
            prefix = ""
            if existing_match.url == match.url:
                prefix = click.style("OLD: ", fg="red", bold=True)
            cal.add_to_date(
                existing_match.date_time, prefix +
                format.short_form_match(existing_match)
            )
        cal.add_to_date(
            moved.date_time,
            click.style("NEW: ", fg="green", bold=True) +
            format.short_form_match(match),
        )

    click.echo(click.style(cal.first.format("MMMM"),
               fg="green", bold=True, underline=True))
    click.echo(
        tabulate.tabulate(
            cal.render(),
            headers=["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            tablefmt="rounded_grid",
        )
    )
