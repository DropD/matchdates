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
        [[location.name, location.address.replace("\n", ", ")] for location in locations],
        headers=["Name", "Address"]
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
    matches.sort(key=lambda m: m.date)
    click.echo(format.tabulate_match_dates(
        matches
    ))
