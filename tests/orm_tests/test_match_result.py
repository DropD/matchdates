import re

from matchdates import orm


def test_create_matchresult(db_session, matchdate, singles_result, doubles_result):
    testee = orm.result.MatchResult(
        match_date=matchdate,
        winner=None,
        walkover=False,
        home_points=0,
        away_points=0
    )
    db_session.add_all([singles_result, doubles_result])
    db_session.commit()

    assert testee.match_date.match_result == testee


def test_render(db_session, match_result):
    db_session.add(match_result)
    db_session.commit()

    lines = match_result.render().splitlines()
    assert lines[0].startswith(
        "BC Zürich-Affoltern 1 vs BC Zürich-Affoltern 2")
    assert re.match(
        r"\s*HE1\s*Anders Antonsen\s*w\s*Kodai Naraoke\s*21:13 24:22",
        lines[3]
    )
    assert re.match(
        r"\s*DD1\s*Line Christophersen / Mia Blichfeldt\s*"
        r"Akane Yamaguchi / Arisa Higashino\s*w\s*19:21 19:21",
        lines[8]
    )


def test_update_match_result(db_session, match_result):
    db_session.add(match_result)
    db_session.commit()

    testee = orm.result.MatchResult.one(id=match_result.id)
    testee.home_points = 0
    testee.away_points = 3
    testee.winner = orm.result.WinningTeam.AWAY
    testee.walkover = True

    db_session.add(match_result)
    db_session.commit()

    assert testee.walkover
