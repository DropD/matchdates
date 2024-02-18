import datetime
import pendulum


def date_to_datetime(date: pendulum.Date, timezone: str | pendulum.Timezone = "Europe/Zurich") -> pendulum.DateTime:
    return pendulum.datetime(year=date.year, month=date.month, day=date.day, tz=timezone)


def enhance(std_datetime: datetime.datetime, timezone: str | pendulum.Timezone = "Europe/Zurich") -> pendulum.DateTime:
    return pendulum.instance(std_datetime, tz=timezone)


def fromiso(datestring: str, timezone: str | pendulum.Timezone) -> pendulum.DateTime:
    return pendulum.DateTime.fromisoformat(datestring).in_timezone(timezone)


def iso_to_std_datetime(datestring: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(datestring)
