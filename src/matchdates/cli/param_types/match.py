import click
import sqlalchemy as sqla

from matchdates import orm


class Match(click.ParamType):
    name = "Match"

    def convert(
        self, value: str | int | orm.MatchDate, param: click.Parameter, ctx: click.Context
    ) -> orm.MatchDate:
        if isinstance(value, orm.MatchDate):
            return value

        match_nr = int(value)
        # TODO: provide a way to distinguish between matches in different seasons
        #      with the same matchnr.
        try:
            match = orm.MatchDate.one(url=f"team-match/{match_nr}")
        except sqla.exc.NoResultFound:
            self.fail(f"No match with nr {value} found!", param, ctx)
        except sqla.exc.MultipleResultsFound:
            self.fail(
                f"more than one match with nr {value} found!", param, ctx)

        return match
