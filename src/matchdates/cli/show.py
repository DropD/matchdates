import collections

import click
import tabulate

from .. import models, date_utils
from .main import main
from . import param_types


@main.group("show")
def show():
    """Display detailed information about matches and locations"""


def _style_info_table(info_table: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return map(
        lambda item: (click.style(item[0], bold=True), item[1]),
        info_table
    )


@show.command("match")
@click.argument("match", type=param_types.match.Match())
def match(match: models.MatchDate) -> None:
    """Display info about a match"""
    location = match.location.fetch()
    click.echo(click.style(f"{match.home_team} vs. {match.away_team}", bold=True, underline=True))
    click.echo("")
    click.echo(tabulate.tabulate(
        _style_info_table(
            [
                ("Time:", date_utils.enhance(match.date).format("dd, DD.MM.YYYY")),
                ("Url:", "https://sb.tournamentsoftware.com" + match.url),
                ("MatchNr:", match.url.rsplit("/")[-1]),
                ("Location Name:", location.name),
                ("Address:", location.address),
            ]
        ),
        tablefmt="plain"
    ))


@show.command("location")
@click.argument("location", type=param_types.location.Location())
def location(location: models.Location) -> None:
    """Display info about a location."""
    info = models.MatchDate.collection.aggregate([
        {"$match": {"location": location.pk}},
        {"$group": {
            "_id": None,
            "teams": {"$addToSet": "$home_team"},
            "dates": {"$addToSet": "$date"}
        }}
    ]).next()

    times = collections.Counter([date_utils.enhance(d).time() for d in info["dates"]])
    
    time_info: str
    match len(times):
        case 1:
            time_info = str(list(times.keys())[0])
        case 2 | 3:
            time_info = tabulate.tabulate(
                [(f"{count}", "x", time.format("HH:mm")) for time, count in times.most_common()],
                tablefmt="plain"
            )
        case _:
            time_info = f"{min(times.keys())} - {max(times.keys())}"
            if (usual_time := times.most_common(1)[0])[1] > times.total() / 5:
                time_info += f", usually {usual_time[0]}"

    click.echo(click.style(
        location.name, bold=True, underline=True
    ))
    click.echo("")
    click.echo(tabulate.tabulate(
        _style_info_table(
            [
                ("Address:", location.address),
                ("", ""),
                ("Home Teams:", "\n".join(sorted(info["teams"]))),
                ("", ""),
                ("Match Times:", time_info)
            ]
        ),
        tablefmt="plain"
    ))
