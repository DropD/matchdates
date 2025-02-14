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
        elif from_url := orm.Season.one_or_none(url=value):
            return from_url
        scores = sorted(
            ((fuzz.ratio(value, s.url), s) for s in orm.Season.all()),
            key=lambda i: i[0],
            reverse=True
        )
        if scores[0][0] - scores[1][0] > 0.1:
            return scores[0][1]
        else:
            candidate_str = "\n".join(
                f"  - {i[1].url} (score: {i[0]})" for i in scores[:3])
            self.fail(
                f"Could not find a Season based on '{value}', did you mean one of the following?\n{candidate_str}"
            )
