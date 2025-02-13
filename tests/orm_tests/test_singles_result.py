from matchdates import common_data, orm


def test_create_singles_result(db_session, matchdate, team1, team2, anas, kodai):

    db_session.add_all([anas, kodai, matchdate])
    db_session.commit()

    testee = orm.result.SinglesResult(
        match_date=matchdate,
        category=common_data.ResultCategory.HE1,
    )
    db_session.add(testee)
    db_session.commit()
    home_player_result = orm.result.HomePlayerResult(
        player=anas,
        singles_result=testee,
        set_1_points=21,
        set_2_points=24,
        win=True
    )
    db_session.add(home_player_result)
    away_player_result = orm.result.AwayPlayerResult(
        player=kodai,
        singles_result=testee,
        set_1_points=13,
        set_2_points=22,
        win=False
    )
    db_session.add(away_player_result)
    db_session.commit()

    assert testee.category is common_data.ResultCategory.HE1
    assert testee.home_player == anas
    assert testee.away_player == kodai
    assert matchdate.home_team in testee.home_player.teams
    assert matchdate.away_team in testee.away_player.teams


def test_backrefs(db_session, singles_result, matchdate, kodai, anas):
    db_session.add(singles_result)
    db_session.commit()

    assert singles_result.home_player_result in anas.home_singles_results
    assert singles_result.away_player_result in kodai.away_singles_results
    assert singles_result in matchdate.singles_results


def test_str(singles_result):
    assert str(singles_result) == (
        "HE1: Anders Antonsen vs. Kodai Naraoke - 21:13 24:22"
    )
