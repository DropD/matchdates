import pendulum
import pytest

from matchdates import orm
from matchdates.orm.base import Base


@pytest.fixture(autouse=True, scope="session")
def db_context():
    ctx = orm.db.DbContext.push("sqlite:///:memory:")
    yield ctx
    orm.db.DbContext.pop()


@pytest.fixture()
def db_engine(db_context):
    engine = db_context.engine
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_context, db_engine):
    session = db_context.session
    yield session
    session.close()


@pytest.fixture
def location():
    yield orm.location.Location(
        name="Badcity Badminton Center",
        address="\n".join(
            ["Badminton Street 1", "0001 Badcity", "Badmintonia"]),
    )


@pytest.fixture
def season():
    yield orm.season.Season(url="season/12345")


@pytest.fixture
def club(season):
    yield orm.club.Club(name="BC Zürich-Affoltern", seasons=[season])


@pytest.fixture
def team1(club, season):
    yield orm.team.Team(name="BC Zürich-Affoltern 1", team_nr=1, club=club, seasons=[season])


@pytest.fixture
def team2(club, season):
    yield orm.team.Team(name="BC Zürich-Affoltern 2", team_nr=2, club=club, seasons=[season])


@pytest.fixture
def matchdate(location, team1, team2, season):
    yield orm.matchdate.MatchDate(
        url="league/12345/match/1",
        date_time=pendulum.now() + pendulum.Duration(days=7),
        location=location,
        home_team=team1,
        away_team=team2,
        season=season,
    )
