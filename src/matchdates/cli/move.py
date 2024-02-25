import click
import pendulum
import tabulate
from typing import Optional

from .. import format, models, queries
from .. import cli
from . import calendar, param_types
from .main import main


@main.command("move")
@click.argument("match", type=param_types.match.Match())
@click.option("--date", type=param_types.date.Date())
@click.option("--time", type=str)
def move(match: models.MatchDate, date: Optional[pendulum.Date], time: Optional[str]) -> None:
    """
    Pretend to move a match and show the new and old date in calendar context.

    Does not actually move anything. Does not modify the local database. 
    Definitely does not do anything on the Swiss-Badminton system.
    """
    time = time or match.date.format("HH:mm")
    date = date or pendulum.instance(match.date).date()
    match.date = pendulum.DateTime.fromisoformat(f"{date.isoformat()} {time}")
    cal = calendar.Month(first=match.date.start_of("month"))
    matches = models.MatchDate.find(
        queries.match_filter_from_to_day(
            start=cal.first,
            end=cal.last
        )
    )
    for existing_match in matches:
        prefix = ""
        if existing_match.url == match.url:
            prefix = click.style("OLD: ", fg="red", bold=True)
        cal.add_to_date(existing_match.date, prefix + format.short_form_match(existing_match))
    cal.add_to_date(
        match.date,
        click.style("NEW: ", fg="green", bold=True) + format.short_form_match(match)
    )
        
    click.echo(click.style(cal.first.format("MMMM"), fg="green", bold=True, underline=True))
    click.echo(
        tabulate.tabulate(
            cal.render(),
            headers=["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], tablefmt="rounded_grid"
        )
    )
