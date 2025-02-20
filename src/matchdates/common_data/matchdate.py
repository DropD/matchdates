import attrs
import cattrs
import pendulum


@cattrs.register_unstructure_hook
def unstructure_date(val: pendulum.Date) -> str:
    return val.to_date_string()


@cattrs.register_unstructure_hook
def unstructure_datetime(val: pendulum.DateTime) -> str:
    return val.isoformat()


@cattrs.register_structure_hook
def structure_date(val: str, _) -> pendulum.Date:
    return pendulum.Date.fromisoformat(val)


@cattrs.register_structure_hook
def structure_datetime(val: str, _) -> pendulum.DateTime:
    return pendulum.DateTime.fromisoformat(val)


@attrs.define
class Season:
    url: str
    name: str
    start_date: pendulum.Date
    end_date: pendulum.Date


@attrs.define
class Draw:
    url: str


@attrs.define
class Location:
    name: str
    address: str


@attrs.define
class Club:
    name: str


@attrs.define
class Team:
    name: str
    url: str
    club: Club


@attrs.define
class MatchDate:
    url: str
    date: pendulum.DateTime
    home_team: Team
    away_team: Team
    location: Location | None = None
    season: Season | None = None
    draw: Draw | None = None
