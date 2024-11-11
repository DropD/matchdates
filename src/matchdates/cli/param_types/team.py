import click
from thefuzz import fuzz

from matchdates import orm


class Team(click.ParamType):
    name = "Team"

    def __init__(self):
        self.case_sensitive = True

    def convert(
        self,
        value: str | orm.Team,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> orm.Team:
        if isinstance(value, orm.Team):
            return value
        elif from_name := orm.Team.one_or_none(name=value):
            return from_name
        candidates = [t for t in orm.Team.all() if value in t.name]
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            candidate_str = "\n".join(f"  - {c.name}" for c in candidates)
            self.fail(
                f"Could not disambiguate teams based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
        else:
            scores = sorted(
                ((fuzz.ratio(value, t.name), t) for t in orm.Team.all()),
                key=lambda i: i[0],
                reverse=True,
            )
            candidate_str = "\n".join(f"  - {i[1].name} (score: {i[0]})" for i in scores[:3])
            self.fail(
                f"Could not find a team based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
