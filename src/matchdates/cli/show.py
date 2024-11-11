import collections

import click
import pendulum
import tabulate
import sqlalchemy as sqla

from .. import orm
from .main import main
from . import param_types


@main.group("show")
def show():
    """Display detailed information about matches and locations"""


def _style_info_table(info_table: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return map(lambda item: (click.style(item[0], bold=True), item[1]), info_table)


@show.command("match")
@click.argument("match", type=param_types.match.Match())
def match(match: orm.MatchDate) -> None:
    """Display info about a match"""
    with orm.db.get_session() as session:
        location = match.location
        click.echo(
            click.style(
                f"{match.home_team.name} vs. {match.away_team.name}", bold=True, underline=True
            )
        )
        click.echo("")
        click.echo(
            tabulate.tabulate(
                _style_info_table(
                    [
                        ("Time:", match.local_date_time.format(
                            "dd, DD.MM.YYYY HH:mm")),
                        ("Url:", match.full_url),
                        ("MatchNr:", match.url.rsplit("/")[-1]),
                        ("Location Name:", location.name),
                        ("Address:", location.address),
                    ]
                ),
                tablefmt="plain",
            )
        )


@show.command("location")
@click.argument("location", type=param_types.location.Location())
def location(location: orm.Location) -> None:
    """Display info about a location."""
    with orm.db.get_session() as session:
        teams = set(m.home_team.name for m in location.match_dates)
        times = collections.Counter(m.local_date_time.time()
                                    for m in location.match_dates)

        time_info: str
        match len(times):
            case 1:
                time_info = str(list(times.keys())[0])
            case 2 | 3:
                time_info = tabulate.tabulate(
                    [
                        (f"{count}", "x", time.format("HH:mm"))
                        for time, count in times.most_common()
                    ],
                    tablefmt="plain",
                )
            case _:
                time_info = f"{min(times.keys())} - {max(times.keys())}"
                if (usual_time := times.most_common(1)[0])[1] > times.total() / 5:
                    time_info += f", usually {usual_time[0]}"

    click.echo(click.style(location.name, bold=True, underline=True))
    click.echo("")
    click.echo(
        tabulate.tabulate(
            _style_info_table(
                [
                    ("Address:", location.address),
                    ("", ""),
                    ("Home Teams:", "\n".join(sorted(teams))),
                    ("", ""),
                    ("Match Times:", time_info),
                ]
            ),
            tablefmt="plain",
        )
    )


@show.command("team")
@click.argument("team", type=param_types.team.Team())
def team(team: orm.Team) -> None:
    with orm.db.get_session() as session:
        home_locations = set(m.location.name for m in team.home_dates)
        all_matches = sorted(
            [*team.home_dates, *team.away_dates], key=lambda m: m.local_date_time)
        upcoming = tabulate.tabulate(
            [
                (m.local_date_time.format("dd YYYY-MM-DD"), m.full_url)
                for m in all_matches
                if m.local_date_time >= pendulum.now()
            ]
        )
        nr_upcoming = len(
            [m for m in all_matches if m.local_date_time >= pendulum.now()])
        club = team.club.name
        seasons = [s.url for s in team.seasons]

    click.secho(team.name, bold=True, underline=True)
    click.echo("")
    click.echo(
        tabulate.tabulate(
            _style_info_table(
                [
                    ("Club:", club),
                    ("", ""),
                    ("Seasons:", seasons),
                    ("", ""),
                    ("Locations", home_locations),
                    ("", ""),
                    (f"Upcoming Matches ({nr_upcoming})", upcoming),
                ]
            )
        )
    )
