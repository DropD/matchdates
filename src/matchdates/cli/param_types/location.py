import click
from thefuzz import fuzz

from matchdates import orm


class Location(click.ParamType):
    name = "Location"

    def __init__(self):
        self.case_sensitive = True

    def convert(
        self,
        value: str | orm.Location,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> orm.Location:
        if isinstance(value, orm.Location):
            return value
        if loc := orm.Location.one_or_none(name=value):
            return loc
        scores = sorted(
            ((fuzz.ratio(value, loc.name), loc)
             for loc in orm.Location.all()),
            key=lambda i: i[0],
            reverse=True,
        )
        if len(scores) == 1:
            return scores[0][1]
        elif len(scores) > 1 and scores[0][0] - scores[1][0] > 5:
            return scores[0][1]
        else:
            candidate_str = "\n".join(f"  - {i[1].name}" for i in scores[:3])
            self.fail(
                f"Could not find a location based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
