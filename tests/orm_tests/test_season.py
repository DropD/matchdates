from matchdates import orm


def test_create_season(db_session):
    seas = orm.season.Season(url="season/1sfd2345")

    db_session.add(seas)
    db_session.commit()

    assert isinstance(seas.id, int)
