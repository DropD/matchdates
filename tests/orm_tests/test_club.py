from matchdates import orm


def test_create_club(db_session):
    club = orm.club.Club("Badcity Badminton Club")
    db_session.add(club)
    db_session.commit()

    assert isinstance(club.id, int)


def test_add_team(db_session):
    club = orm.club.Club("Badcity Badminton Club")
    team = orm.team.Team("Badcity Badminton Club 4",
                         4, url="team/1", club=None)
    club.teams.append(team)

    db_session.add(club)
    db_session.commit()

    assert isinstance(club.id, int)
    assert isinstance(team.id, int)
    assert team in club.teams
    assert team.club == club


def test_add_season(db_session, season):
    club = orm.club.Club("Badcity Badminton Club")
    club.seasons.append(season)

    db_session.add(club)
    db_session.commit()

    assert isinstance(club.id, int)
    assert isinstance(season.id, int)
    assert season in club.seasons
    assert club in season.clubs
