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

        scores = sorted(
            ((fuzz.ratio(value, t.name), t) for t in orm.Team.all()),
            key=lambda i: i[0],
            reverse=True,
        )
        if len(scores) == 1:
            return scores[0][1]
        elif len(scores) > 1 and scores[0][0] - scores[1][0] > 5:
            return scores[0][1]
        else:
            candidate_str = "\n".join(
                f"  - {i[1].name} (score: {i[0]})" for i in scores[:3])
            self.fail(
                f"Could not find a team based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
