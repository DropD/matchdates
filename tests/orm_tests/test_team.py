from matchdates import orm


def test_create_team(db_session, club):
    team = orm.team.Team(name="BC Zürich-Affoltern 1",
                         url="team/1", team_nr=1, club=club)
    db_session.add_all([team, club])
    db_session.commit()

    assert isinstance(team.id, int)
    assert team.club == club
    assert team in club.teams
