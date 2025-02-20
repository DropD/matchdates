import pytest
import pendulum

from matchdates import common_data as cd, data2orm, orm


@pytest.fixture
def converter(db_session) -> data2orm.matchdate.MatchdateToOrm:
    return data2orm.matchdate.MatchdateToOrm(session=db_session)


def test_visit_location(db_session, converter):
    loc = converter.visit(
        cd.Location(
            name="foo",
            address="Foostr 23\n1234 Barstadt"
        )
    )
    db_session.commit()
    assert isinstance(loc.id, int)
    assert loc.name == "foo"
    assert loc.address == "Foostr 23\n1234 Barstadt"


def test_visit_location_existing(db_session, converter, location):
    db_session.add(location)
    db_session.commit()
    n_locs_ref = len(orm.Location.all())
    loc = converter.visit(
        cd.Location(
            name=location.name,
            address=location.address + "\nChanged"
        )
    )
    db_session.commit()
    assert len(orm.Location.all()) == n_locs_ref
    assert "Changed" in orm.Location.one(name=loc.name).address


def test_visit_season(db_session, converter):
    season = converter.visit(
        cd.Season(
            name="Test Season",
            url="season/123",
            start_date=pendulum.Date(2000, 9, 1),
            end_date=pendulum.Date(2001, 4, 30)
        )
    )
    db_session.commit()
    assert isinstance(season.id, int)
    assert season.name == "Test Season"


def test_visit_season_existing(db_session, converter, season):
    season = converter.visit(
        cd.Season(
            name="Test Season 2024-25",
            url="season/12345",
            start_date=pendulum.Date(2024, 8, 1),
            end_date=pendulum.Date(2025, 5, 30)
        )
    )
    db_session.commit()
    assert isinstance(season.id, int)
    assert season.end_date.day == 30


def test_visit_draw(db_session, converter, season):
    db_session.add(season)
    db_session.commit()
    draw = converter.visit(
        cd.Draw(
            url="draw/2"
        ),
        season=season
    )
    db_session.commit()
    assert isinstance(draw.id, int)
    assert draw.season == season
    assert draw in season.draws


def test_visit_draw_existing(db_session, converter, draw):
    db_session.add(draw)
    db_session.commit()
    n_draws_ref = len(orm.Draw.all())
    new_draw = converter.visit(
        cd.Draw(
            url="draw/1"
        ),
        season=draw.season
    )
    db_session.commit()
    assert len(orm.Draw.all()) == n_draws_ref
    assert len(draw.season.draws) == 1


def test_visit_team(db_session, converter, club, draw):
    db_session.add_all([club, draw])
    db_session.commit()
    new_team = converter.visit(
        cd.Team(
            name=f"{club.name} 2",
            url="team/213",
            club=cd.Club(club.name)
        ),
        draw=draw
    )
    db_session.commit()
    assert isinstance(new_team.id, int)
    assert draw.season in new_team.seasons
    assert new_team in draw.season.teams
    assert draw in new_team.draws
    assert len(new_team.draws) == 1
    assert new_team in draw.teams
    assert new_team.club == club


def test_visit_team_existing(db_session, converter, team1, draw):
    db_session.add(team1)
    db_session.commit()
    n_teams_ref = len(orm.Team.all())
    new_team = converter.visit(
        cd.Team(
            name=team1.name,
            url=f"team/{team1.team_nr}",
            club=cd.Club(team1.club.name)),
        draw=draw
    )
    db_session.commit()
    assert len(orm.Team.all()) == n_teams_ref
    assert len(draw.season.teams) == 1
    assert len(new_team.seasons) == 1
    assert len(new_team.draws) == 1
    assert len(draw.teams) == 1
    assert len(new_team.club.teams) == 1


def test_visit_matchdate(db_session, converter):
    new_matchdate = converter.visit(
        cd.MatchDate(
            url="team-match/42",
            date=pendulum.now(),
            home_team=cd.Team(
                url="team/1",
                name="Home 1",
                club=cd.Club("Home")
            ),
            away_team=cd.Team(
                url="team/2",
                name="Away 1",
                club=cd.Club("Away")
            ),
            location=cd.Location("Foo", "Barstr. 1"),
            draw=cd.Draw("draw/1"),
            season=cd.Season(
                name="Testseason",
                url="season/1",
                start_date=pendulum.Date(1, 1, 1),
                end_date=pendulum.Date(1, 12, 31),
            )
        )
    )
    db_session.commit()
    assert isinstance(new_matchdate.id, int)
    assert new_matchdate.season.teams == [
        new_matchdate.home_team, new_matchdate.away_team
    ]
    assert new_matchdate.season.clubs == [
        new_matchdate.home_team.club, new_matchdate.away_team.club
    ]
    assert new_matchdate.season.draws == [new_matchdate.draw]
    assert not new_matchdate.changelog


def test_visit_matchdate_update(db_session, converter, matchdate):
    db_session.add(matchdate)
    db_session.commit()
    new_matchdate = converter.visit(
        cd.MatchDate(
            url=matchdate.url,
            date=matchdate.date_time + pendulum.duration(hours=1),
            home_team=cd.Team(
                url=matchdate.home_team.url,
                name=matchdate.home_team.name,
                club=cd.Club(matchdate.home_team.club.name)
            ),
            away_team=cd.Team(
                url=matchdate.away_team.url,
                name=matchdate.away_team.name,
                club=cd.Club(matchdate.away_team.club.name)
            ),
            location=cd.Location(
                matchdate.location.name, matchdate.location.address
            ),
            draw=cd.Draw(matchdate.draw.url),
            season=cd.Season(
                name=matchdate.season.name,
                url=matchdate.season.url,
                start_date=matchdate.season.start_date,
                end_date=matchdate.season.end_date
            )
        )
    )
    db_session.commit()
    assert new_matchdate.id == matchdate.id
    assert (matchdate.local_date_time -
            matchdate.last_change.local_date_time).in_hours() == 1
