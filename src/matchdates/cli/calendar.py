import dataclasses

import click
import pendulum
import tabulate
import sqlalchemy as sqla

from .. import models, queries, format, orm
from .main import main


@dataclasses.dataclass
class Month:
    first: pendulum.date
    cells: dict[int, list[str]] = dataclasses.field(default_factory=dict)
    normal_style = {"fg": "black", "bg": "white"}
    today_style = {"fg": "white", "bg": "red"}

    @property
    def year(self) -> int:
        return self.first.year

    @property
    def month(self) -> int:
        return self.first.month

    @property
    def last(self) -> pendulum.date:
        return self.first.last_of(unit="month")

    def add_to_date(self, date: pendulum.date, *lines: str) -> None:
        if date.year == self.year and date.month == self.month:
            self.cells.setdefault(date.day, []).extend(lines)

    def render(self) -> list[list[str]]:
        cal = [[""] * 7 for i in range(self.last.week_of_month)]
        for day in range(1, self.last.day):
            date = pendulum.date(self.year, self.month, day)

            lines = [
                click.style(
                    f"{day:<24}",
                    **(self.today_style if date == pendulum.Date.today() else self.normal_style),
                )
            ]
            if day in self.cells:
                lines += self.cells[day]
            week = date.week_of_month - 1
            weekday = date.weekday()
            cal[week][weekday] = "\n".join(lines)
        return cal


@main.command("calendar")
@click.argument("month", type=int, default=pendulum.now().month)
@click.option("--rules", type=str, default="all")
@click.option("--year", type=int, default=pendulum.now().year)
def calendar(month, rules, year):
    """Display calendar view of matches."""
    cal = Month(first=pendulum.now().replace(month=month, year=year, day=1))
    matches = list(
        models.MatchDate.find(queries.match_filter_from_to_day(start=cal.first, end=cal.last))
    )
    for match in matches:
        postfix = ""
        needsfix = click.style("X", fg="red", bold=True)
        if rules == "all":
            if (
                pendulum.WeekDay(match.date.weekday()) == pendulum.WEDNESDAY
                and match.home_team.startswith("BC Zürich-Affoltern")
                and not match.home_team.endswith("S")
            ):
                postfix = needsfix
            elif match.date.month == 4 and match.date.day > 17:
                postfix = needsfix
        cal.add_to_date(match.date, format.short_form_match(match) + " " + postfix)

    click.echo(click.style(cal.first.format("MMMM"), fg="green", bold=True, underline=True))
    click.echo(
        tabulate.tabulate(
            cal.render(),
            headers=["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            tablefmt="rounded_grid",
        )
    )


@main.command("calendar-sqlite")
@click.argument("month", type=int, default=pendulum.now().month)
@click.option("--rules", type=str, default="all")
@click.option("--year", type=int, default=pendulum.now().year)
def calendar_sqlite(month, rules, year):
    """Display calendar view of matches."""
    session = sqla.orm.Session(orm.db.get_db())
    cal = Month(first=pendulum.now().replace(month=month, year=year, day=1))
    matches = (
        session.query(orm.MatchDate)
        .filter(orm.MatchDate.date_time > cal.first, orm.MatchDate.date_time < cal.last)
        .all()
    )
    bcza = session.query(orm.Club).filter_by(name="BC Zürich-Affoltern").one_or_none()
    for match in matches:
        postfix = ""
        needsfix = click.style("X", fg="red", bold=True)
        if rules == "all":
            if (
                pendulum.WeekDay(match.local_date_time.weekday()) == pendulum.WEDNESDAY
                and match.home_team.club == bcza
                and not match.home_team.team_nr == "S"
            ):
                postfix = needsfix
            elif match.local_date_time.month == 4 and match.local_date_time.day > 17:
                postfix = needsfix
        cal.add_to_date(match.local_date_time, format.short_form_orm_match(match) + " " + postfix)

    click.echo(click.style(cal.first.format("MMMM"), fg="green", bold=True, underline=True))
    click.echo(
        tabulate.tabulate(
            cal.render(),
            headers=["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
            tablefmt="rounded_grid",
        )
    )
