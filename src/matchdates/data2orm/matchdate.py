from __future__ import annotations

import dataclasses
import enum
import functools
from typing import Any

import sqlalchemy as sqla

from matchdates import common_data as cd, orm


class Change(enum.Enum):
    DATE = enum.auto()
    LOCATION = enum.auto()


def url_segment(url: str, start: int | None, stop: int | None) -> str:
    return "/".join(url.strip("/").split("/")[start:stop])


@dataclasses.dataclass
class MatchdateToOrm:
    session: sqla.orm.Session

    @functools.singledispatchmethod
    def visit(self, node: Any, **kwargs: Any) -> orm.Base | None:
        raise NotImplementedError

    @visit.register
    def visit_season(self, node: cd.Season, **kwargs: Any) -> orm.Season:
        url = url_segment(node.url, -2, None)
        season = orm.Season.one_or_none(
            url=url) or orm.Season(
            url=url,
            name=node.name,
            start_date=node.start_date,
            end_date=node.end_date
        )
        season.name = node.name
        season.start_date = node.start_date
        season.end_date = node.end_date
        self.session.add(season)
        return season

    @visit.register
    def visit_draw(
        self,
        node: cd.Draw,
        *,
        season: orm.Season,
        **kwargs: Any
    ) -> orm.Draw:
        url = url_segment(node.url, -2, None)
        draw = orm.Draw.one_or_none(
            url=url, season=season
        ) or orm.Draw(url=url, season=season)
        self.session.add(draw)
        return draw

    @visit.register
    def visit_location(
        self, node: cd.Location, **kwargs: Any
    ) -> orm.Location:
        location = orm.Location.one_or_none(
            name=node.name
        ) or orm.Location(name=node.name, address=node.address)
        location.address = node.address
        self.session.add(location)
        return location

    @visit.register
    def visit_team(
        self, node: cd.Team, *, draw: cd.Draw, **kwargs: Any
    ) -> orm.Team:
        club = orm.Club.one_or_none(
            name=node.club.name) or orm.Club(name=node.club.name)

        last_name_part = node.name.rsplit(" ", 1)[-1]
        team_nr = int(last_name_part) if last_name_part.isdigit() else 1

        url = url_segment(node.url, -2, None)
        team = orm.Team.one_or_none(
            name=node.name
        ) or orm.Team(
            name=node.name,
            url=url,
            team_nr=team_nr,
            club=club
        )
        team.url = url
        team.club = club
        if draw not in team.draws:
            team.draws.append(draw)
        if draw.season not in team.seasons:
            team.seasons.append(draw.season)
        if draw.season not in club.seasons:
            club.seasons.append(draw.season)

        self.session.add(team)
        return team

    @visit.register
    def visit_matchdate(
        self, node: cd.MatchDate, **kwargs: Any
    ) -> orm.MatchDate:
        season = self.visit(node.season)
        draw = self.visit(node.draw, season=season)
        location = self.visit(node.location)
        url = url_segment(node.url, -2, None)
        matchdate = orm.MatchDate.one_or_none(
            url=url, season=season
        ) or orm.MatchDate(
            url=url,
            date_time=node.date,
            location=location,
            season=season,
            home_team=self.visit(node.home_team, draw=draw),
            away_team=self.visit(node.away_team, draw=draw)
        )

        matchdate.draw = draw
        matchdate.update_with_history(
            new_date_time=node.date,
            new_location=location
        )

        self.session.add(matchdate)
        self.session.commit()
        return matchdate
