import pendulum

from matchdates import orm


def test_create_season(db_session):
    seas = orm.season.Season(
        name="Testee Season",
        url="season/1sfd2345",
        start_date=pendulum.Date(2024, 8, 1),
        end_date=pendulum.Date(2025, 5, 31)
    )

    db_session.add(seas)
    db_session.commit()

    assert isinstance(seas.id, int)
