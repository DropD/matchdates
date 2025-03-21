import click
from thefuzz import fuzz

from matchdates import orm


class Season(click.ParamType):
    name = "Season"

    def __init__(self):
        self.case_sensitive = False

    def convert(
        self, value: str | orm.Season,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> orm.Season:
        if isinstance(value, orm.Season):
            return value
        elif value == "current":
            return orm.Season.current()
        elif from_url := orm.Season.one_or_none(name=value):
            return from_url
        scores = sorted(
            ((fuzz.ratio(value, s.name), s) for s in orm.Season.all()),
            key=lambda i: i[0],
            reverse=True
        )
        if len(scores) == 1:
            return scores[0][1]
        elif len(scores) > 1 and scores[0][0] - scores[1][0] > 1:
            return scores[0][1]
        else:
            candidate_str = "\n".join(
                f"  - {i[1].name} (score: {i[0]})" for i in scores[:3])
            self.fail(
                f"Could not find a Season based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
