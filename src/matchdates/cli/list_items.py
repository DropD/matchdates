import dataclasses
from typing import Optional

import click
import pendulum
import tabulate
import sqlalchemy as sqla

from .. import format, orm
from .main import main
from . import param_types


@main.group("list")
def list_items():
    """List entities."""


@list_items.command("teams")
def teams():
    """List teams"""
    with orm.db.get_session() as session:
        team_names = [
            [i] for i in session.scalars(sqla.select(orm.Team.name)).all()
        ]
    team_names.sort()
    click.echo(tabulate.tabulate(team_names))


@list_items.command("urls")
def urls():
    """List match urls"""
    items = [[f"/{m.season.url}/{m.url}"] for m in orm.MatchDate.all()]
    items.sort(key=lambda item: item[0])
    click.echo(tabulate.tabulate(items))
    session.close()


@list_items.command("locations")
def locations():
    """List Locations"""
    locations = orm.Location.all()
    locations.sort(key=lambda loc: loc.name)
    click.echo(
        tabulate.tabulate(
            [[location.name, location.address.replace(
                "\n", ", ")] for location in locations],
            headers=["Name", "Address"],
        )
    )


def player_names(player: orm.Player) -> tuple[str, str]:
    match player.name.split(" "):
        case[first, last]:
            return (first, last)
        case[first, second, last]:
            return (f"{first} {second}", last)
        case[first, second, last1, last2]:
            return (f"{first} {second}", f"{last1} {last2}")
        case[*components]:
            return (" ".join(components[:2]), " ".join(components[2:]))
        case _:
            return (player.name, "")


def players_by_team(team: Optional[orm.Team]) -> None:

    @dataclasses.dataclass
    class PlayerRow:
        last: str
        first: str
        player_nr: str
        events: int
        matches: int

    click.echo(f"Players for Team {team}")

    players = orm.Player.filter(orm.player.by_team(team))
    matches_by_team = orm.MatchDate.filter(orm.matchdate.by_team(team))
    player_table = {}
    headers = [
        "Name",
        "SB Nr",
        "Nr Events for Team",
        "Nr Events Total",
        "Nr Matches for Team",
        "Nr Matches Total"
    ]
    for player in players:
        row = []
        row.append(player.name)
        row.append(player.player_nr)
        filtered_by_player = [
            m for m in matches_by_team if orm.matchdate.player_in_match_for_team(player, m, team)]
        row.append(len(filtered_by_player))
        singles_results = player.home_singles_results + player.away_singles_results
        singles_events = set(
            r.singles_result.match_date.id for r in singles_results)
        doubles_results = [i for j in
                           [p.home_doubles_results + p.away_doubles_results for p in player.doubles_pairs] for i in j]
        doubles_events = set(
            r.doubles_result.match_date.id for r in doubles_results
        )
        row.append(len(singles_events | doubles_events))
        results_for_team = []
        for m in filtered_by_player:
            for r in singles_results:
                if r.singles_result in m.singles_results:
                    results_for_team.append(r)
            for d in doubles_results:
                if d.doubles_result in m.doubles_results:
                    results_for_team.append(d)
        row.append(len(results_for_team))
        row.append(len(singles_results + doubles_results))
        season_key = str(filtered_by_player[0].season)
        player_table.setdefault(season_key, [])
        player_table[season_key].append(row)
        for k, v in player_table.items():
            v.sort(key=lambda row: (row[2], row[4]), reverse=True)
            click.echo(f"\nSeason {k}:")
            click.echo(tabulate.tabulate(v, headers=headers))


@list_items.command("players")
@click.option("--by-team", type=param_types.team.Team(), default=None)
@click.pass_context
def players(ctx, by_team: orm.Team | None) -> None:
    """List Players"""
    if by_team:
        players_by_team(by_team)
        ctx.exit(0)
    with orm.db.get_session():
        players = orm.Player.all()

        players.sort(key=lambda player: player_names(player)[1])
    click.echo(
        tabulate.tabulate(
            [
                [(names := player_names(player))[1],
                 names[0], player.url.rsplit("/", 1)[1]]
                for player in players
            ],
            headers=["Last", "First", "player_nr"],
        )
    )


# TODO: make an orm team param type
# TODO: make an orm location param type
@list_items.command("matches")
@click.option("--by-team", type=param_types.team.Team(), default=None)
@click.option("--by-location", type=param_types.location.Location(), default=None)
def matches(by_team: Optional[orm.Team], by_location: Optional[orm.Location]):
    """List matches"""
    matches: list[orm.MatchDate]
    with orm.db.get_session() as session:
        if by_team:
            matches = orm.MatchDate.filter(
                orm.MatchDate.home_team.has(id=by_team.id)
                | orm.MatchDate.away_team.has(id=by_team.id)
            )
        elif by_location:
            location = orm.Location.one(name=by_location.name)
            matches = orm.MatchDate.filter_by(location=location)
        else:
            matches = orm.MatchDate.all()
        matches.sort(key=lambda m: m.local_date_time)
        click.echo(format.tabulate_match_dates(matches))


@list_items.command("results")
@click.option("--by-team", type=param_types.team.Team(), default=None)
@click.option("--by-season", type=param_types.season.Season(), default=None)
def results(by_team: orm.Team | None, by_season: orm.Season | None):
    """List Match results."""
    results: list[orm.MatchResult]
    with orm.db.get_session() as session:
        must_filter = any([by_team, by_season])
        if must_filter:
            filters = None
            if by_team:
                filters = orm.matchdate.by_team(by_team)
            if by_season:
                if filters is None:
                    filters = orm.matchdate.by_season(by_season)
                else:
                    filters &= orm.matchdate.by_season(by_season)
            matches = orm.MatchDate.filter(
                filters & orm.MatchDate.match_result)

            results = [m.match_result for m in matches]
        else:
            results = orm.MatchResult.all()
        results.sort(key=lambda r: r.match_date.local_date_time)
        click.echo(format.tabulate_match_results(results))


@list_items.command("seasons")
def seasons():
    click.echo(tabulate.tabulate(
        [
            [
                s.name,
                f"{s.start_date} - {s.end_date}",
                s.url
            ] for s in orm.Season.all()
        ]
    ))
