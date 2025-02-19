import pytest

from matchdates import common_data as cd, data2orm, orm


@pytest.fixture
def players_ab() -> tuple[cd.Player, cd.Player]:
    player_a = cd.Player(name="A", url="l/1/player/1")
    player_b = cd.Player(name="B", url="l/1/player/2")
    return player_a, player_b


@pytest.fixture
def players_cd() -> tuple[cd.Player, cd.Player]:
    player_c = cd.Player(name="C", url="l/1/player/3")
    player_d = cd.Player(name="D", url="l/1/player/4")
    return player_c, player_d


@pytest.fixture
def team_result() -> cd.TeamMatchResult:
    # player urls must match the ones from the top level conftest
    anas = cd.Player(name="Anders Antonsen", url="l/1/player/1")
    kodai = cd.Player(name="Kodai Naraoke", url="l/1/player/2")
    victor = cd.Player(name="Victor Axelsen", url="l/1/player/3")
    yuta = cd.Player(name="Yuta Watanabe", url="l/1/player/4")
    rasmus = cd.Player(name="Rasmus Gemke", url="l/1/player/5")
    line = cd.Player(name="Line Christophersen", url="l/1/player/6")
    mia = cd.Player(name="Mia Blichfeldt", url="l/1/player/7")
    endo = cd.Player(name="Endo Kirakawa", url="l/1/player/8")
    akane = cd.Player(name="Akane Yamaguchi", url="l/1/player/9")
    arisa = cd.Player(name="Arisa Higashino", url="l/1/player/10")
    return cd.TeamMatchResult(
        singles={
            cd.ResultCategory.HE1: cd.SinglesResult(
                home_player=anas,
                away_player=kodai,
                set_1=cd.Set(14, 21),
                set_2=cd.Set(21, 19),
                set_3=cd.Set(5, 21),
                winner=cd.Side.AWAY
            ),
            cd.ResultCategory.HE2: cd.SinglesResult(
                home_player=victor,
                away_player=yuta,
                set_1=cd.Set(21, 3),
                set_2=cd.Set(21, 18),
                winner=cd.Side.HOME
            ),
            cd.ResultCategory.HE3: cd.SinglesResult(
                home_player=rasmus,
                away_player=endo,
                set_1=cd.Set(21, 17),
                set_2=cd.Set(21, 14),
                winner=cd.Side.HOME
            ),
            cd.ResultCategory.DE1: cd.SinglesResult(
                home_player=mia,
                away_player=akane,
                set_1=cd.Set(19, 21),
                set_2=cd.Set(19, 21),
                winner=cd.Side.AWAY
            )
        },
        doubles={
            cd.ResultCategory.HD1: cd.DoublesResult(
                home_pair=cd.DoublesPair(anas, victor),
                away_pair=cd.DoublesPair(yuta, kodai),
                set_1=cd.Set(14, 21),
                set_2=cd.Set(21, 19),
                set_3=cd.Set(5, 21),
                winner=cd.Side.AWAY
            ),
            cd.ResultCategory.DD1: cd.DoublesResult(
                home_pair=cd.DoublesPair(line, mia),
                away_pair=cd.DoublesPair(akane, arisa),
                set_1=cd.Set(19, 21),
                set_2=cd.Set(19, 21),
                winner=cd.Side.AWAY
            ),
            cd.ResultCategory.MX1: cd.DoublesResult(
                home_pair=cd.DoublesPair(rasmus, line),
                away_pair=cd.DoublesPair(endo, arisa),
                set_1=cd.Set(21, 17),
                set_2=cd.Set(21, 18),
                winner=cd.Side.HOME
            )
        },
        url="league/12345/match/1",
        winner=cd.Side.AWAY
    )


def make_empty_singles(winner: cd.Side) -> cd.SinglesResult:
    return cd.SinglesResult(
        home_player=None,
        away_player=None,
        winner=winner,
    )


def make_empty_doubles(winner: cd.Side) -> cd.DoublesResult:
    return cd.DoublesResult(
        home_pair=None,
        away_pair=None,
        winner=winner
    )


def test_count_wins(players_ab):
    testee = data2orm.results.count_wins(
        [
            cd.SinglesResult(
                home_player=players_ab[0],
                away_player=players_ab[1],
                set_1=cd.Set(21, 12),
                set_2=cd.Set(21, 16),
                winner=cd.Side.HOME
            ),
            make_empty_doubles(cd.Side.AWAY)
        ]
    )
    assert testee[cd.Side.HOME] == 1
    assert testee[cd.Side.AWAY] == 1


def test_team_match_points_ul():
    testee = data2orm.results.team_match_points(
        data2orm.results.count_wins(
            ([make_empty_singles(cd.Side.HOME)] * 4)
            + ([make_empty_doubles(cd.Side.AWAY)] * 3)
        )
    )
    assert testee[cd.Side.HOME] == 2
    assert testee[cd.Side.AWAY] == 1


def test_team_match_points_sl():
    testee = data2orm.results.team_match_points(
        data2orm.results.count_wins(
            [make_empty_doubles(cd.Side.HOME)] * 2
            + [make_empty_doubles(cd.Side.AWAY)] * 2
        )
    )
    assert testee[cd.Side.HOME] == 2
    assert testee[cd.Side.AWAY] == 2


def test_visit_singles_result(db_session, matchdate, players_ab):
    db_session.add(matchdate)
    db_session.commit()
    testee = data2orm.results.ResultToOrm(
        session=db_session, matchdate=matchdate
    )
    player_a, player_b = players_ab
    twosets = testee.visit(
        cd.SinglesResult(
            home_player=player_a,
            away_player=player_b,
            set_1=cd.Set(21, 12),
            set_2=cd.Set(23, 21),
            winner=cd.Side.HOME
        ),
        category=cd.ResultCategory.HE1
    )
    threesets = testee.visit(
        cd.SinglesResult(
            home_player=player_a,
            away_player=player_b,
            set_1=cd.Set(5, 21),
            set_2=cd.Set(21, 9),
            set_3=cd.Set(25, 27),
            winner=cd.Side.AWAY
        ),
        category=cd.ResultCategory.HE2
    )
    retired = testee.visit(
        cd.SinglesResult(
            home_player=player_a,
            away_player=player_b,
            set_1=cd.Set(13, 15),
            retired=cd.Side.AWAY,
            winner=cd.Side.HOME
        ),
        category=cd.ResultCategory.HE3
    )
    walkover = testee.visit(
        make_empty_singles(cd.Side.AWAY),
        category=cd.ResultCategory.DE1
    )

    assert twosets.winner is cd.Side.HOME
    assert twosets.home_player.name == "A"
    assert twosets.home_player.teams == [matchdate.home_team]
    assert twosets.away_player.name == "B"
    assert twosets.away_player.teams == [matchdate.away_team]
    assert twosets.home_player_result.set_1_points == 21
    assert twosets.away_player_result.set_2_points == 21
    assert twosets.home_player_result.set_3_points is twosets.away_player_result.set_3_points is None

    assert threesets.winner is cd.Side.AWAY
    assert threesets.home_player.teams == [matchdate.home_team]
    assert threesets.away_player.teams == [matchdate.away_team]

    assert retired.home_player_result.set_2_points is None
    assert retired.away_player_result.set_2_points is None
    assert retired.winner is cd.Side.HOME

    assert walkover.home_player_result is None
    assert walkover.away_player_result is None
    assert walkover.walkover_winner is cd.Side.AWAY


def test_visit_doubles_result(db_session, matchdate, players_ab, players_cd):
    db_session.add(matchdate)
    db_session.commit()

    player_a, player_b = players_ab
    player_c, player_d = players_cd
    pair_a = cd.DoublesPair(player_a, player_b)
    pair_c = cd.DoublesPair(player_c, player_d)

    testee = data2orm.results.ResultToOrm(
        session=db_session, matchdate=matchdate
    )

    standard = testee.visit(
        cd.DoublesResult(
            home_pair=pair_a,
            away_pair=pair_c,
            set_1=cd.Set(21, 14),
            set_2=cd.Set(21, 14),
            winner=cd.Side.HOME
        ),
        category=cd.ResultCategory.HD2
    )
    assert standard.winner is cd.Side.HOME
    assert standard.home_pair_result.set_1_points == 21
    assert standard.away_pair_result.set_2_points == 14
    assert standard.home_pair.teams == [matchdate.home_team]
    assert standard.away_pair.teams == [matchdate.away_team]

    missing_player = testee.visit(
        cd.DoublesResult(
            home_pair=cd.DoublesPair(player_a, None),
            away_pair=pair_c,
            set_1=cd.Set(21, 14),
            set_2=cd.Set(21, 14),
            winner=cd.Side.HOME
        ),
        category=cd.ResultCategory.HD1
    )
    assert missing_player.winner is cd.Side.HOME
    assert missing_player.home_pair_result is None
    assert missing_player.away_pair_result is None

    walkover = testee.visit(
        make_empty_doubles(cd.Side.AWAY), category=cd.ResultCategory.DD1
    )
    assert walkover.walkover_winner is cd.Side.AWAY

    retired = testee.visit(
        cd.DoublesResult(
            home_pair=pair_a,
            away_pair=pair_c,
            set_1=cd.Set(1, 0),
            winner=cd.Side.HOME,
            retired=cd.Side.AWAY
        ),
        category=cd.ResultCategory.MX1
    )

    assert retired.winner is cd.Side.HOME
    assert retired.home_pair.teams == [matchdate.home_team]
    assert retired.away_pair.teams == [matchdate.away_team]


def test_visit_result(db_session, matchdate, team_result):
    db_session.add(matchdate)
    db_session.commit()
    testee = data2orm.results.ResultToOrm(
        session=db_session, matchdate=matchdate
    )
    testee.visit(team_result)
    assert matchdate.match_result.winner == orm.result.WinningTeam.AWAY
    assert matchdate.match_result.home_points == 1
    assert matchdate.match_result.away_points == 2
    assert len(matchdate.singles_results) == 4
    assert len(matchdate.doubles_results) == 3


def test_visit_update_result(db_session, matchdate, team_result, match_result):
    db_session.add(matchdate)
    db_session.add(match_result)
    db_session.commit()
    ref_nr_team_results = len(orm.MatchResult.all())
    ref_nr_singles_results = len(orm.SinglesResult.all())
    ref_nr_doubles_results = len(orm.DoublesResult.all())
    ref_nr_players = len(orm.Player.all())
    ref_nr_pairs = len(orm.DoublesPair.all())

    testee = data2orm.results.ResultToOrm(
        session=db_session, matchdate=matchdate
    )
    testee.visit(team_result)
    assert matchdate.match_result.id == match_result.id
    assert len(matchdate.singles_results) == 4
    assert len(matchdate.doubles_results) == 3
    assert len(orm.MatchResult.all()) == ref_nr_team_results
    assert len(orm.SinglesResult.all()) == ref_nr_singles_results
    assert len(orm.DoublesResult.all()) == ref_nr_doubles_results
    assert len(orm.Player.all()) == ref_nr_players
    assert len(orm.DoublesPair.all()) == ref_nr_pairs
