import datetime
import pendulum
from pendulum.tz.timezone import Timezone


def date_to_datetime(date: pendulum.Date, timezone: str | Timezone = "Europe/Zurich") -> pendulum.DateTime:
    return pendulum.datetime(year=date.year, month=date.month, day=date.day, tz=timezone)


def enhance(std_datetime: datetime.datetime, timezone: str | Timezone = "Europe/Zurich") -> pendulum.DateTime:
    return pendulum.instance(std_datetime, tz=timezone)
