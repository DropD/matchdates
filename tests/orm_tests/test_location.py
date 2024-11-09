import pendulum
import pytest

from matchdates import orm


def test_create_location(db_session):
    loc = orm.location.Location(
        name="Blumenfeldhalle", address="Blumenfeldstrasse 50\n8046 Zürich")
    db_session.add(loc)
    db_session.commit()
    assert isinstance(loc.id, int)
    assert loc.match_dates == []


def test_create_no_address(db_session):
    with pytest.raises(TypeError, match=r".*missing 1 required positional argument: 'address'"):
        _ = orm.location.Location(name="Blumenfeldhalle")


def test_create_no_name(db_session):
    with pytest.raises(TypeError, match=r".*missing 1 required positional argument: 'name'"):
        _ = orm.location.Location(address="8046 Zürich")


def test_add_matchdate(db_session, location):
    mdt = orm.matchdate.MatchDate(
        url="asdfasdf", date_time=pendulum.now() + pendulum.duration(days=7)
    )
    location.match_dates.append(mdt)
    db_session.commit()
    assert mdt in location.match_dates
    assert mdt.location == location
