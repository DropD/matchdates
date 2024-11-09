from typing import Optional

import click

from matchdates import models


class Location(click.Choice):
    name = "Location"

    def __init__(self):
        self.case_sensitivee = True

    @property
    def choices(self):
        return [loc.name for loc in models.Location.find({})]

    def convert(
        self,
        value: str | models.Location,
        param: Optional[click.Parameter],
        ctx: Optional[click.Context],
    ) -> models.Location:
        return models.Location.find_one({"name": value})
