import click
from thefuzz import fuzz

from matchdates import models, orm


class Location(click.ParamType):
    name = "Location"

    def __init__(self):
        self.case_sensitive = True

    def convert(
        self,
        value: str | orm.Location,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> models.Location:
        if isinstance(value, orm.Location):
            return value
        if loc := orm.Location.one_or_none(name=value):
            return loc
        candidates = [loc for loc in orm.Location.all() if value in loc.name]
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            candidate_str = "\n".join(f"  - {c.name}" for c in candidates)
            self.fail(
                f"Could not disambiguate locations based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
        else:
            scores = sorted(
                ((fuzz.ratio(value, loc.name), loc) for loc in orm.Location.all()),
                key=lambda i: i[0],
                reverse=True,
            )
            candidate_str = "\n".join(f"  - {i[1].name}" for i in scores[:3])
            self.fail(
                f"Could not find a location based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
