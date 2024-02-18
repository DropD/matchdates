import dataclasses
import difflib
import enum
from typing import Optional

import pendulum
import pymongo
import umongo
import umongo.frameworks
from typing_extensions import Self
from umongo import fields

from . import date_utils


def get_db() -> pymongo.database.Database:
    client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
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
            changeset.append(f"{self.location.fetch()} -> {match.location.fetch()}")
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
                existing.address.splitlines(),
                address.splitlines(),
                fromfile="old",
                tofile="new"
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
                archivation_date=pendulum.now()
            )
            existing.update(
                {
                    "date": date,
                    "location": location
                }
            )
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
            url=url,
            date=date,
            home_team=home_team,
            away_team=away_team,
            location=location
        )
        new.commit()
        return MatchDateFromDataResult(
            match_date=new,
            status=DocumentFromDataStatus.NEW,
            change_reasons=[]
        )
