import pendulum
import sqlalchemy as sqla

from matchdates import orm


def test_create_matchdate_minimal(db_session, location, season):
    mdt = orm.matchdate.MatchDate(
        url="league/23234/match/234",
        date_time=pendulum.now() + pendulum.Duration(days=7),
        location=location,
        season=season
    )
    db_session.add(mdt)
    db_session.commit()

    assert isinstance(mdt.id, int)


def test_create_matchdate_full(db_session, location, team1, team2, season):
    mdt = orm.matchdate.MatchDate(
        url="league/12345/match/1",
        date_time=pendulum.now() + pendulum.Duration(days=7),
        location=location,
        home_team=team1,
        away_team=team2,
        season=season
    )
    db_session.add(mdt)
    db_session.commit()

    assert mdt.location == location
    assert mdt in location.match_dates
    assert mdt.home_team == team1
    assert mdt.away_team == team2
    assert mdt in team1.home_dates
    assert mdt in team2.away_dates


def test_update_datetime(db_session, matchdate):
    db_session.add(matchdate)
    db_session.commit()

    new_dt = pendulum.now()

    loaded = db_session.get(orm.matchdate.MatchDate, matchdate.id)
    loaded.date_time = new_dt
    db_session.commit()

    reloaded = db_session.get(orm.matchdate.MatchDate, matchdate.id)
    assert reloaded.local_date_time == new_dt


def test_update_location(db_session, matchdate):
    db_session.add(matchdate)
    db_session.commit()

    new_loc = orm.location.Location(
        name="Bedminton Court", address="Dhuni Kolhu")

    loaded = db_session.get(orm.matchdate.MatchDate, matchdate.id)
    loaded.location = new_loc
    db_session.commit()

    reloaded = db_session.get(orm.matchdate.MatchDate, matchdate.id)
    assert reloaded.location == new_loc


def test_update_with_history(db_session, matchdate):
    db_session.add(matchdate)
    db_session.commit()

    old_dt = matchdate.local_date_time
    old_loc = matchdate.location
    new_dt = pendulum.now()
    new_loc = orm.location.Location(
        name="Bedminton Court", address="Dhuni Kolhu"
    )

    matchdate.update_with_history(
        new_date_time=new_dt, new_location=new_loc
    )
    db_session.commit()

    reloaded = db_session.get(orm.matchdate.MatchDate, matchdate.id)
    assert reloaded.location == new_loc
    assert reloaded.local_date_time == new_dt
    assert reloaded.changelog[0].location == old_loc
    assert reloaded.changelog[0].local_date_time == old_dt
