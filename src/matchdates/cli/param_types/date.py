import click
import pendulum


class Date(click.ParamType):
    name = "Date"

    def convert(
        self,
        value: str | pendulum.Date,
        param: click.Parameter,
        ctx: click.Context
    ) -> pendulum.Date:
        match value:
            case str():
                return pendulum.Date.fromisoformat(value)
            case pendulum.Date():
                return value
            case _:
                return pendulum.Date.fromisoformat(str(value))
