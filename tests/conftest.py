import pendulum
import pytest

from matchdates import orm, common_data
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


@pytest.fixture
def anas(team1):
    yield orm.player.Player(url="player/1", name="Anders Antonsen", teams=[team1])


@pytest.fixture
def kodai(team2):
    yield orm.player.Player(url="player/2", name="Kodai Naraoke", teams=[team2])


@pytest.fixture
def victor(team1):
    yield orm.player.Player(url="player/3", name="Victor Axelsen", teams=[team1])


@pytest.fixture
def yuta(team2):
    yield orm.player.Player(url="player/4", name="Yuta Watanabe", teams=[team2])


@pytest.fixture
def singles_result(matchdate, anas, kodai):
    singlesresult = orm.result.SinglesResult(
        match_date=matchdate,
        category=common_data.ResultCategory.HE1,
    )
    home_player_result = orm.result.HomePlayerResult(
        player=anas,
        singles_result=singlesresult,
        set_1_points=21,
        set_2_points=24,
        win=True
    ),
    away_player_result = orm.result.AwayPlayerResult(
        player=kodai,
        singles_result=singlesresult,
        set_1_points=13,
        set_2_points=22,
        win=False
    )
    yield singlesresult


@pytest.fixture
def doubles_result(matchdate, anas, kodai, victor, yuta):
    doublesresult = orm.result.DoublesResult(
        match_date=matchdate,
        category=common_data.ResultCategory.HD1,
    )
    home_pair = orm.player.DoublesPair(players={anas, victor})
    away_pair = orm.player.DoublesPair(players={kodai, yuta})
    home_pair_result = orm.result.HomePairResult(
        doubles_pair=home_pair,
        doubles_result=doublesresult,
        set_1_points=14,
        set_2_points=21,
        set_3_points=5
    )
    away_pair_result = orm.result.AwayPairResult(
        doubles_pair=away_pair,
        doubles_result=doublesresult,
        set_1_points=21,
        set_2_points=19,
        set_3_points=21
    )
    yield doublesresult


@pytest.fixture
def match_result(matchdate, singles_result, doubles_result, anas, kodai, victor, yuta):
    rasmus = orm.player.Player(
        url="player/5", name="Rasmus Gemke", teams=[matchdate.home_team])
    line = orm.player.Player(
        url="player/6", name="Line Christophersen", teams=[matchdate.home_team])
    mia = orm.player.Player(
        url="player/7", name="Mia Blichfeldt", teams=[matchdate.home_team])
    endo = orm.player.Player(
        url="player/8", name="Endo Kirakawa", teams=[matchdate.away_team])
    akane = orm.player.Player(
        url="player/9", name="Akane Yamaguchi", teams=[matchdate.away_team])
    arisa = orm.player.Player(
        url="player/10", name="Arisa Higashino", teams=[matchdate.away_team])
    rasmus_line = orm.player.DoublesPair(players={rasmus, line})
    endo_arisa = orm.player.DoublesPair(players={endo, arisa})
    line_mia = orm.player.DoublesPair(players={line, mia})
    akane_arisa = orm.player.DoublesPair(players={akane, arisa})

    he2 = orm.result.SinglesResult(
        match_date=matchdate, category=common_data.ResultCategory.HE2)
    he3 = orm.result.SinglesResult(
        match_date=matchdate, category=common_data.ResultCategory.HE3)
    de1 = orm.result.SinglesResult(
        match_date=matchdate, category=common_data.ResultCategory.DE1)
    dd1 = orm.result.DoublesResult(
        match_date=matchdate, category=common_data.ResultCategory.DD1)
    xd1 = orm.result.DoublesResult(
        match_date=matchdate, category=common_data.ResultCategory.MX1)

    he2_h = orm.result.HomePlayerResult(
        player=victor,
        singles_result=he2,
        set_1_points=21,
        set_2_points=21
    )
    he2_a = orm.result.AwayPlayerResult(
        player=yuta,
        singles_result=he2,
        set_1_points=3,
        set_2_points=18
    )

    he3_h = orm.result.HomePlayerResult(
        player=rasmus,
        singles_result=he3,
        set_1_points=21,
        set_2_points=21
    )
    he3_a = orm.result.AwayPlayerResult(
        player=endo,
        singles_result=he3,
        set_1_points=17,
        set_2_points=14
    )

    de1_h = orm.result.HomePlayerResult(
        player=mia,
        singles_result=de1,
        set_1_points=14,
        set_2_points=11
    )
    de1_a = orm.result.AwayPlayerResult(
        player=akane,
        singles_result=de1,
        set_1_points=21,
        set_2_points=21
    )

    dd1_h = orm.result.HomePairResult(
        doubles_pair=line_mia,
        doubles_result=dd1,
        set_1_points=19,
        set_2_points=19
    )
    dd1_a = orm.result.AwayPairResult(
        doubles_pair=akane_arisa,
        doubles_result=dd1,
        set_1_points=21,
        set_2_points=21
    )

    xd1_h = orm.result.HomePairResult(
        doubles_pair=rasmus_line,
        doubles_result=xd1,
        set_1_points=21,
        set_2_points=21
    )
    xd1_a = orm.result.AwayPairResult(
        doubles_pair=endo_arisa,
        doubles_result=xd1,
        set_1_points=17,
        set_2_points=18
    )

    yield orm.result.MatchResult(
        match_date=matchdate,
        winner=orm.result.WinningTeam.HOME,
        walkover=False,
        home_points=2,
        away_points=1
    )
