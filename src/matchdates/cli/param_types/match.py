import click

from matchdates import models, orm


class Match(click.ParamType):
    name = "Match"

    def convert(
        self, value: str | int | models.MatchDate, param: click.Parameter, ctx: click.Context
    ) -> models.MatchDate:
        if isinstance(value, models.MatchDate):
            return value

        match_nr = int(value)
        match = orm.MatchDate.one(url=f"team-match/{match_nr}")
        if not match:
            self.fail(f"No match with nr {value} found!", param, ctx)

        return match
