import pytest

from matchdates import orm


def test_create_player(db_session):
    player = orm.Player(url="player/1234", name="Anders Antonsen")
    db_session.add(player)
    db_session.commit()

    assert isinstance(player.id, int)
    assert player.doubles_pairs == []


def test_create_doubles_pair(db_session):
    wata = orm.Player(url="player/1", name="Yuta Watanabe")
    higa = orm.Player(url="player/2", name="Arisa Higashino")
    pair = orm.DoublesPair(players={wata, higa})
    db_session.add_all([wata, higa, pair])
    db_session.commit()

    assert isinstance(pair.id, int)
    assert wata in pair.players
    assert higa in pair.players
    assert pair in wata.doubles_pairs
    assert pair in higa.doubles_pairs
    assert db_session.scalars(
        orm.DoublesPair.select().filter(
            orm.DoublesPair.players.contains(wata)
            & orm.DoublesPair.players.contains(higa)
        )
    ).one_or_none()


def test_from_players(db_session):
    wata = orm.Player(url="player/1", name="Yuta Watanabe")
    higa = orm.Player(url="player/2", name="Arisa Higashino")
    pair = orm.DoublesPair(players={wata, higa})
    db_session.add_all([wata, higa, pair])
    db_session.commit()
    reloaded = orm.DoublesPair.from_players(wata, higa)
    assert reloaded.id == pair.id


def test_fail_create_doubles_triple(db_session):
    wata = orm.Player(url="player/1", name="Yuta Watanabe")
    higa = orm.Player(url="player/2", name="Arisa Higashino")
    aya = orm.Player(url="player/3", name="Aya Ohori")
    with pytest.raises(ValueError):
        pair = orm.DoublesPair(players={wata, higa, aya})
        db_session.add_all([wata, higa, aya, pair])
        db_session.commit()


def test_fail_add_third_player(db_session):
    wata = orm.Player(url="player/1", name="Yuta Watanabe")
    higa = orm.Player(url="player/2", name="Arisa Higashino")
    aya = orm.Player(url="player/3", name="Aya Ohori")
    pair = orm.DoublesPair(players={wata, higa})
    with pytest.raises(ValueError):
        pair.players.add(aya)


@pytest.mark.filterwarnings("ignore:Object of type <DoublesPair> not in session")
def test_fail_create_duplicate_to_stored(db_session):
    wata = orm.Player(url="player/1", name="Yuta Watanabe")
    higa = orm.Player(url="player/2", name="Arisa Higashino")
    pair = orm.DoublesPair(players={wata, higa})
    db_session.add_all([wata, higa, pair])
    db_session.commit()
    with pytest.raises(ValueError):
        _ = orm.DoublesPair({wata, higa})
    with pytest.raises(ValueError):
        _ = orm.DoublesPair({higa, wata})
