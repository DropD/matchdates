import click

from ... import models, queries


class Team(click.Choice):
    name = "Team"

    def __init__(self):
        self.case_sensitive = True

    @property
    def choices(self):
        return models.MatchDate.collection.aggregate([
                queries.match_list_field_values("home_team")
            ]).next()["teams"]
