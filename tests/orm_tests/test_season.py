from matchdates import orm


def test_create_season():
    seas = orm.season.Season(url="season/12345")
