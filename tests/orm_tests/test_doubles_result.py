from matchdates import orm


def test_create_doubles_result(
    db_session, matchdate, team1, team2, anas, kodai, victor, yuta
):
    matchdate.home_team.players.extend([anas, victor])
    matchdate.away_team.players.extend([kodai, yuta])
    home_pair = orm.player.DoublesPair(players={anas, victor})
    away_pair = orm.player.DoublesPair(players={kodai, yuta})
    db_session.add_all([matchdate, home_pair, away_pair])
    db_session.commit()

    testee = orm.result.DoublesResult(
        match_date=matchdate,
        category=orm.result.ResultCategory.HD1,
        home_pair_result=None,
        away_pair_result=None
    )
    home_pair_result = orm.result.HomePairResult(
        doubles_pair=home_pair,
        doubles_result=testee,
        set_1_points=16,
        set_2_points=21,
        set_3_points=5,
        win=False
    )
    away_pair_result = orm.result.AwayPairResult(
        doubles_pair=away_pair,
        doubles_result=testee,
        set_1_points=21,
        set_2_points=19,
        set_3_points=21,
        win=True
    )
    db_session.add_all([testee, home_pair_result, away_pair_result])
    db_session.commit()

    assert testee.category is orm.result.ResultCategory.HD1
    assert testee.home_pair == home_pair
    assert testee.away_pair == away_pair
    assert testee in matchdate.doubles_results


def test_backrefs(db_session, doubles_result, matchdate):
    db_session.add(doubles_result)
    db_session.commit()
    home_pair = doubles_result.home_pair
    away_pair = doubles_result.away_pair
    assert doubles_result.home_pair_result in home_pair.home_doubles_results
    assert doubles_result.away_pair_result in away_pair.away_doubles_results
    assert doubles_result in matchdate.doubles_results


def test_str(doubles_result):
    assert str(doubles_result) == (
        "HD1: Anders Antonsen / Victor Axelsen vs. "
        "Kodai Naraoke / Yuta Watanabe - 14:21 21:19 5:21"
    )
