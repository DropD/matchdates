import dataclasses
import difflib
import enum
import logging
import textwrap
from typing import Optional, Iterator

import pendulum
import pymongo
import umongo
import umongo.frameworks
import tabulate
from umongo import fields, validate

from . import date_utils
from . import settings


SETTINGS = settings.SETTINGS["database"]


def get_db() -> pymongo.database.Database:
    client = pymongo.MongoClient(SETTINGS["mongodb"])
    logging.getLogger("pymongo.command").setLevel(logging.WARN)
    logging.getLogger("pymongo.serverSelection").setLevel(logging.WARN)
    return client.matchdates


def get_instance() -> umongo.frameworks.PyMongoInstance:
    return umongo.frameworks.PyMongoInstance(get_db())


INSTANCE = get_instance()


@INSTANCE.register
class Location(umongo.Document):
    name = fields.StringField(required=True, unique=True)
    address = fields.StringField()

    def __str__(self) -> str:
        return f"{self.name} @ {self.address.splitlines()[0]}..."


@INSTANCE.register
class MatchDate(umongo.Document):
    url = fields.StringField(required=True, unique=True)
    date = fields.DateTimeField(required=True)
    home_team = fields.StringField(required=True)
    away_team = fields.StringField(required=True)
    location = fields.ReferenceField(Location)

    def __str__(self) -> str:
        return (
            f"{self.home_team} vs {self.away_team} on {self.date} at {self.location.fetch().name}"
        )

    @property
    def matchnr(self) -> str:
        return self.url.rsplit("/", 1)[1]


@INSTANCE.register
class Player(umongo.Document):
    url = fields.StringField(required=True, unique=True)
    name = fields.StringField(required=True)

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash((self.url, self.name))


@INSTANCE.register
class DoublesPair(umongo.Document):
    first = fields.ReferenceField(Player)
    second = fields.ReferenceField(Player)

    def __str__(self) -> str:
        return f"{self.first.fetch()} / {self.second.fetch()}"

    @property
    def players(self):
        return [self.first.fetch(), self.second.fetch()]


@INSTANCE.register
class Set(umongo.EmbeddedDocument):
    home_points = fields.IntegerField(validate=validate.Range(min=0, max=30))
    away_points = fields.IntegerField(validate=validate.Range(min=0, max=30))

    def __str__(self) -> str:
        return f"{self.home_points} : {self.away_points}"


@INSTANCE.register
class SinglesResult(umongo.EmbeddedDocument):
    home_player = fields.ReferenceField(Player, allow_none=True)
    away_player = fields.ReferenceField(Player, allow_none=True)
    set_1 = fields.EmbeddedField(Set, allow_none=True)
    set_2 = fields.EmbeddedField(Set, allow_none=True)
    set_3 = fields.EmbeddedField(Set, allow_none=True)
    home_won = fields.BoolField(required=True)

    @property
    def sets(self) -> Iterator[Set]:
        if self.set_1:
            yield self.set_1
        if self.set_2:
            yield self.set_2
        if self.set_3:
            yield self.set_3

    @property
    def table_row(self) -> list:
        return [
            self.home_player.fetch(),
            "w" if self.home_won else "",
            self.away_player.fetch(),
            "w" if not self.home_won else "",
            *self.sets,
        ]

    @property
    def players(self) -> dict[str, list[str]]:
        return {
            "away": [self.away_player.fetch()] if self.away_player else [],
            "home": [self.home_player.fetch()] if self.home_player else [],
        }

    def __str__(self) -> str:
        score_str = " | ".join(str(set) for set in self.sets)
        match self.home_won:
            case True:
                return f"{self.home_player.fetch()} (w) vs. {self.away_player.fetch()} {score_str}"
            case False:
                return f"{self.home_player.fetch()} vs. {self.away_player.fetch()} (w) {score_str}"


@INSTANCE.register
class DoublesResult(umongo.EmbeddedDocument):
    home_pair = fields.ReferenceField(DoublesPair, allow_none=True)
    away_pair = fields.ReferenceField(DoublesPair, allow_none=True)
    set_1 = fields.EmbeddedField(Set, allow_none=True)
    set_2 = fields.EmbeddedField(Set, allow_none=True)
    set_3 = fields.EmbeddedField(Set, allow_none=True)
    home_won = fields.BoolField(required=True)

    @property
    def sets(self) -> Iterator[Set]:
        if self.set_1:
            yield self.set_1
        if self.set_2:
            yield self.set_2
        if self.set_3:
            yield self.set_3

    @property
    def table_row(self) -> list:
        return [
            self.home_pair.fetch(),
            "w" if self.home_won else "",
            self.away_pair.fetch(),
            " " if self.home_won else "w",
            *self.sets,
        ]

    @property
    def players(self) -> dict[str, list[str]]:
        return {
            "away": self.away_pair.fetch().players if self.away_pair else [],
            "home": self.home_pair.fetch().players if self.away_pair else [],
        }

    def __str__(self) -> str:
        score_str = " ".join(str(set) for set in self.sets)
        match self.home_won:
            case True:
                return f"{self.home_pair.fetch()} (w) vs. {self.away_pair.fetch()} {score_str}"
            case False:
                return f"{self.home_pair.fetch()} vs. {self.away_pair.fetch()} (w) {score_str}"


@INSTANCE.register
class MatchResult(umongo.Document):
    match_date = fields.ReferenceField(MatchDate)
    mens_singles_1 = fields.EmbeddedField(SinglesResult)
    mens_singles_2 = fields.EmbeddedField(SinglesResult)
    mens_singles_3 = fields.EmbeddedField(SinglesResult)
    mens_doubles = fields.EmbeddedField(DoublesResult)
    womens_singles = fields.EmbeddedField(SinglesResult)
    womens_doubles = fields.EmbeddedField(DoublesResult)
    mixed_doubles = fields.EmbeddedField(DoublesResult)
    home_won: fields.BoolField(required=True)

    @property
    def events(self) -> Iterator[SinglesResult | DoublesResult]:
        if self.mens_singles_1:
            yield self.mens_singles_1
        if self.mens_singles_2:
            yield self.mens_singles_2
        if self.mens_singles_3:
            yield self.mens_singles_3
        if self.mens_doubles:
            yield self.mens_doubles
        if self.womens_singles:
            yield self.womens_singles
        if self.womens_doubles:
            yield self.womens_doubles
        if self.mixed_doubles:
            yield self.mixed_doubles

    @property
    def event_items(self) -> Iterator[tuple[str, SinglesResult | DoublesResult]]:
        if self.mens_singles_1:
            yield (("mens_singles", 1), self.mens_singles_1)
        if self.mens_singles_2:
            yield (("mens_singles", 2), self.mens_singles_2)
        if self.mens_singles_3:
            yield (("mens_singles", 3), self.mens_singles_3)
        if self.mens_doubles:
            yield (("mens_doubles", None), self.mens_doubles)
        if self.womens_singles:
            yield (("womens_singles", None), self.womens_singles)
        if self.womens_doubles:
            yield (("womens_doubles", None), self.womens_doubles)
        if self.mixed_doubles:
            yield (("mixed_doubles", None), self.mixed_doubles)

    def render(self) -> str:
        results = tabulate.tabulate(
            [
                ["MS1", *self.mens_singles_1.table_row],
                ["MS2", *self.mens_singles_2.table_row],
                ["MS3", *self.mens_singles_3.table_row],
                ["MD", *self.mens_doubles.table_row],
                ["WS", *self.womens_singles.table_row],
                ["WD", *self.womens_doubles.table_row],
                ["XD", *self.mixed_doubles.table_row],
            ]
        )
        return f"{self.match_date.fetch()}\n{textwrap.indent(results, prefix='  ')}"


@INSTANCE.register
class HistoricMatchDate(umongo.Document):
    date = fields.DateTimeField(required=True)
    location = fields.ReferenceField(Location)
    match = fields.ReferenceField(MatchDate)
    archivation_date = fields.DateTimeField(required=True)

    def __str__(self) -> str:
        match = self.match.fetch()
        changeset = []
        self_date = pendulum.instance(self.date)
        match_date = pendulum.instance(match.date)
        if self_date != match_date:
            changeset.append(f"{self_date} -> {match_date}")
        if self.location != match.location:
            changeset.append(
                f"{self.location.fetch()} -> {match.location.fetch()}")
        changes = " ".join(changeset)
        return f"CHANGED: {match.home_team} vs {match.away_team}: {changes}"


class DocumentFromDataStatus(enum.Enum):
    NEW = "document was not yet present in database"
    CHANGED = "document already in database but updated"
    UNCHANGED = "document already in database and unchanged"


class MatchDateChangeReason(enum.Enum):
    DATE = "the date or time was changed"
    LOCATION = "the match was moved to a different location"


@dataclasses.dataclass
class LocationFromDataResult:
    location: Location
    status: DocumentFromDataStatus
    diff: list[str]


@dataclasses.dataclass
class MatchDateFromDataResult:
    match_date: MatchDate
    status: DocumentFromDataStatus
    change_reasons: list[MatchDateChangeReason]
    archive_entry: Optional[HistoricMatchDate] = None


def load_location_from_upstream(name: str, address: str) -> LocationFromDataResult:
    """Find existing location (update if necessary) or add a new one from upstream."""
    existing = Location.find_one({"name": name})
    if existing:
        address_changed = existing.address != address
        if address_changed:
            diff = difflib.unified_diff(
                existing.address.splitlines(), address.splitlines(), fromfile="old", tofile="new"
            )
            existing.update({"address": address})
            existing.commit()
            return LocationFromDataResult(
                location=existing,
                status=DocumentFromDataStatus.CHANGED,
                diff=diff,
            )

        return LocationFromDataResult(
            location=existing,
            status=DocumentFromDataStatus.UNCHANGED,
            diff=[],
        )
    else:
        new = Location(name=name, address=address)
        new.commit()
        return LocationFromDataResult(
            location=new,
            status=DocumentFromDataStatus.NEW,
            diff=[],
        )


def load_match_date_from_upstream(
    *,
    url: str,
    date: str,
    home_team: str,
    away_team: str,
    location: Location,
) -> MatchDateFromDataResult:
    """Find existing match date (update if necessary) or add a new one from upstream."""
    existing = MatchDate.find_one({"url": url})
    date = date_utils.iso_to_std_datetime(date)
    if existing:
        change_reasons = []
        if existing.date != date:
            change_reasons.append(MatchDateChangeReason.DATE)
        if existing.location.fetch() != location:
            change_reasons.append(MatchDateChangeReason.LOCATION)

        if change_reasons:
            archived = HistoricMatchDate(
                date=existing.date,
                location=existing.location,
                match=existing,
                archivation_date=pendulum.now(),
            )
            existing.update({"date": date, "location": location})
            archived.commit()
            existing.commit()
            return MatchDateFromDataResult(
                match_date=existing,
                status=DocumentFromDataStatus.CHANGED,
                change_reasons=change_reasons,
                archive_entry=archived,
            )
        else:
            return MatchDateFromDataResult(
                match_date=existing,
                status=DocumentFromDataStatus.UNCHANGED,
                change_reasons=[],
            )
    else:
        new = MatchDate(
            url=url, date=date, home_team=home_team, away_team=away_team, location=location
        )
        new.commit()
        return MatchDateFromDataResult(
            match_date=new, status=DocumentFromDataStatus.NEW, change_reasons=[]
        )
