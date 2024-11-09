import click

import tabulate

from .. import graph_utils
from . import main


@main.group
def graph():
    """Manage the denormalized data representation."""


@graph.command("update")
def update():
    """Update the internal denormalized data representation."""
    graph_utils.update_results()


@graph.command("affi-players")
def affi_players():
    """Display Players by how often they played for who."""
    affi_teams = list(graph_utils.Team.find({"name": {"$regex": "BC Zürich-Affoltern"}}))
    links = graph_utils.PlayedMatch.find({"team": {"$in": affi_teams}})
    data = {}
    for link in links:
        entry = data.setdefault(link.start.fetch().name, {})
        entry.setdefault("teams", set()).add(link.team.fetch().name.rsplit(" ", 1)[-1])
        entry.setdefault("played", 0)
        entry["played"] += 1
    click.echo(
        tabulate.tabulate(
            sorted(
                [[k, v["teams"], v["played"]] for k, v in data.items()],
                key=lambda row: row[2],
                reverse=True,
            )
        )
    )
