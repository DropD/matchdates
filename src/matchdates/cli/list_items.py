import collections
import dataclasses
from typing import Optional

import click
import tabulate

from .. import models, queries, format
from .main import main
from . import param_types


@main.group("list")
def list_items():
    """List entities."""


@list_items.command("teams")
def teams():
    """List teams"""
    team_names = [
        [i] for i in models.MatchDate.collection.aggregate([
            queries.match_list_field_values("home_team")
        ]).next()["teams"]
    ]
    team_names.sort()
    click.echo(tabulate.tabulate(team_names))


@list_items.command("urls")
def urls():
    """List teams"""
    items = [
        [i] for i in models.MatchDate.collection.aggregate([
            queries.match_list_field_values("url")
        ]).next()["teams"]
    ]
    items.sort(key=lambda item: item[0])
    click.echo(tabulate.tabulate(items))


@list_items.command("locations")
def locations():
    """List Locations"""
    locations = list(models.Location.find({}))
    locations.sort(key=lambda loc: loc.name)
    click.echo(tabulate.tabulate(
        [[location.name, location.address.replace(
            "\n", ", ")] for location in locations],
        headers=["Name", "Address"]
    ))


def player_names(player):
    match player.name.split(" "):
        case [first, last]:
            return (first, last)
        case [first, second, last]:
            return (f"{first} {second}", last)
        case [first, second, last1, last2]:
            return (f"{first} {second}", f"{last1} {last2}")
        case [*components]:
            return (" ".join(components[:2]), " ".join(components[2:]))
        case _:
            return (player.name, "")


def players_by_team(team: Optional[str]) -> None:
    home_matches = list(models.MatchDate.find(
        {"home_team": team}
    ))
    away_matches = list(models.MatchDate.find(
        {"away_team": team}
    ))
    home_results = list(models.MatchResult.find({"match_date": {"$in": home_matches}}))
    away_results = list(models.MatchResult.find({"match_date": {"$in": away_matches}}))

    @dataclasses.dataclass
    class PlayerRow:
        last: str
        first: str
        player_nr: str
        events: int
        matches: int

    collected_players: dict[Player: list[str, str, str, int, int]] = {}
    for results, side in [(home_results, "home"), (away_results, "away")]:
        for result in results:
            seen_players: set[Player] = set()
            for event in result.events:
                for player in event.players[side]:
                    collected_players.setdefault(player, PlayerRow(
                        last=(names := player_names(player))[1],
                        first=names[0],
                        player_nr=player.url.rsplit("/", 1)[1],
                        events=0,
                        matches=0
                    )).events += 1
                    if player not in seen_players:
                        collected_players[player].matches += 1
                    seen_players.add(player)
    player_table = sorted([
        [
            player.last,
            player.first,
            player.player_nr,
            player.events,
            player.matches
        ] for player in collected_players.values()
    ], key=lambda row: (row[-1], row[-2]), reverse=True)
    headers = [
        "Last", "First", "player_nr", "Events Played", "Matches played"
    ]

    click.echo(tabulate.tabulate(player_table, headers=headers))


@list_items.command("players")
@click.option("--by-team", type=param_types.team.Team(), default=None)
@click.pass_context
def players(ctx, by_team: Optional[str]) -> None:
    """List Players"""
    if by_team:
        players_by_team(by_team)
        ctx.exit(0)

    players = list(models.Player.find({}))

    players.sort(key=lambda player: player_names(player)[1])
    click.echo(tabulate.tabulate(
        [[(names := player_names(player))[1], names[0], player.url.rsplit("/", 1)[1]] for player in players],
        headers=["Last", "First", "player_nr"]
    ))


@list_items.command("matches")
@click.option("--by-team", type=param_types.team.Team(), default=None)
@click.option("--by-location", type=param_types.location.Location(), default=None)
def matches(by_team: Optional[str], by_location: Optional[models.Location]):
    """List matches"""
    matches: list[models.MatchDate]
    if by_team:
        matches = list(models.MatchDate.find({
            "$or": [
                {"home_team": by_team},
                {"away_team": by_team},
            ],
        }))
    elif by_location:
        matches = list(models.MatchDate.find({
            "location": by_location
        }))
    else:
        matches = list(models.MatchDate.find({}))
    matches.sort(key=lambda m: m.date)
    click.echo(format.tabulate_match_dates(
        matches
    ))
