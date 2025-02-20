from __future__ import annotations

import dataclasses
import collections
import functools
import typing
from typing import Any, Callable

import sqlalchemy as sqla

from matchdates import common_data, orm


def count_wins(matches: list[common_data.SinglesResult | common_data.DoublesResult]) -> collections.Counter:
    return collections.Counter([m.winner for m in matches])


def team_match_points(win_count: collections.Counter[common_data.Side]) -> dict[common_data.Side, int]:
    nmatches = win_count.total()
    no_points = {common_data.Side.HOME: 0, common_data.Side.AWAY: 0}
    match nmatches:
        case 7:
            return no_points | {side: nwins // 2 for side, nwins in win_count.items()}
        case 4:
            return no_points | dict(win_count)
        case _:
            msg = f"Don't know how to count team points for team events with {nmatches} matches"
            raise NotImplemented(msg)


def update_orm_singles_result(
    orm_result: orm.SinglesResult,
    data_result: common_data.SinglesResult
) -> None:
    for i in range(1, 4):
        data_set = getattr(data_result, f"set_{i}")
        if data_set:
            setattr(orm_result.home_player_result,
                    f"set_{i}_points", data_set.home_points)
            setattr(orm_result.away_player_result,
                    f"set_{i}_points", data_set.away_points)
    orm_result.home_player_result.win = bool(
        data_result.winner == common_data.Side.HOME
    )
    orm_result.away_player_result.win = bool(
        data_result.winner == common_data.Side.AWAY
    )


def update_orm_doubles_result(
    orm_result: orm.SinglesResult,
    data_result: common_data.SinglesResult
) -> None:
    for i in range(1, 4):
        data_set = getattr(data_result, f"set_{i}")
        if data_set:
            setattr(orm_result.home_pair_result,
                    f"set_{i}_points", data_set.home_points)
            setattr(orm_result.away_pair_result,
                    f"set_{i}_points", data_set.away_points)
    orm_result.home_pair_result.win = bool(
        data_result.winner == common_data.Side.HOME
    )
    orm_result.away_pair_result.win = bool(
        data_result.winner == common_data.Side.AWAY
    )


@dataclasses.dataclass
class ResultToOrm:
    session: sqla.orm.Session
    matchdate: orm.MatchDate | None = None

    @functools.singledispatchmethod
    def visit(self, node: Any, **kwargs: Any) -> orm.Base | None:
        raise NotImplementedError

    @visit.register
    def visit_teamresult(self, node: common_data.TeamMatchResult, **kwargs: Any) -> orm.MatchResult:
        """
        Visit all the children and then calculate team match level properties.

        Responsible for
        - not duplicating MatchResults
        """
        url_parts = node.url.split("/")
        season_url = "/".join(url_parts[:2])
        matchdate_url = "/".join(url_parts[2:])
        if not self.matchdate:
            season = orm.Season.one(url=season_url)
            self.matchdate = orm.MatchDate.one(
                url=matchdate_url,
                season=season
            )
        singles_results = [
            self.visit(result, category=category) for category, result
            in node.singles.items()
        ]
        doubles_results = [
            self.visit(result, category=category) for category, result
            in node.doubles.items()
        ]
        team_points = team_match_points(
            count_wins(singles_results + doubles_results)
        )
        winner: orm.result.WinningTeam | None = None
        match node.winner:
            case common_data.Side.HOME:
                winner = orm.result.WinningTeam.HOME
            case common_data.Side.AWAY:
                winner = orm.result.WinningTeam.AWAY
            case _:
                winner = None

        if winner and not singles_results and not doubles_results:
            team_points[node.winner] = 3
            team_points[node.winner.opposite] = 0

        result = orm.MatchResult.one_or_none(
            match_date=self.matchdate
        ) or orm.MatchResult(
            match_date=self.matchdate,
            winner=winner,
            home_points=team_points[common_data.Side.HOME],
            away_points=team_points[common_data.Side.AWAY],
            walkover=bool(not singles_results and not doubles_results)
        )

        result.winner = winner
        result.home_points = team_points[common_data.Side.HOME]
        result.away_points = team_points[common_data.Side.AWAY]
        self.session.add(result)
        self.session.commit()
        return result

    @visit.register
    def visit_singles_result(
        self,
        node: common_data.SinglesResult,
        *,
        category: common_data.ResultCategory,
        **kwargs: Any
    ) -> orm.SinglesResult:
        """
        Convert a singles result.

        Responsible for
         - not duplicating singles results
         - ensuring players are in respective teams
        """

        home_player = self.visit(
            node.home_player) if node.home_player else None
        away_player = self.visit(
            node.away_player) if node.away_player else None

        result = orm.SinglesResult.one_or_none(match_date=self.matchdate, category=category) or orm.SinglesResult(
            match_date=self.matchdate,
            category=category
        )

        if home_player and self.matchdate.home_team not in home_player.teams:
            home_player.teams.append(self.matchdate.home_team)
        if away_player and self.matchdate.away_team not in away_player.teams:
            away_player.teams.append(self.matchdate.away_team)

        if not home_player or not away_player:
            result.walkover_winner = node.winner
        else:
            if not result.home_player_result:
                result.home_player_result = orm.result.HomePlayerResult(
                    player=home_player
                )
            if not result.away_player_result:
                result.away_player_result = orm.result.AwayPlayerResult(
                    player=away_player
                )
            update_orm_singles_result(result, node)
        self.session.add(result)
        return result

    @visit.register
    def visit_doubles_result(
        self,
        node: common_data.DoublesResult,
        *,
        category: common_data.ResultCategory,
        **kwargs: Any
    ) -> orm.DoublesResult:
        """
        Convert a doubles result.

        Responsible for
        - not duplicating doubles results
        - ensuring doubles pairs are in respective teams
        - ensuring players are in respective teams
        """
        home_pair = self.visit(node.home_pair) if node.home_pair else None
        away_pair = self.visit(node.away_pair) if node.away_pair else None

        if home_pair:
            if self.matchdate.home_team not in home_pair.teams:
                home_pair.teams.append(self.matchdate.home_team)
            for player in home_pair.players:
                if self.matchdate.home_team not in player.teams:
                    player.teams.append(self.matchdate.home_team)
        if away_pair:
            if self.matchdate.away_team not in away_pair.teams:
                away_pair.teams.append(self.matchdate.away_team)
            for player in away_pair.players:
                if self.matchdate.away_team not in player.teams:
                    player.teams.append(self.matchdate.away_team)

        result = orm.DoublesResult.one_or_none(
            match_date=self.matchdate, category=category
        ) or orm.DoublesResult(
            match_date=self.matchdate, category=category
        )

        if not home_pair or not away_pair:
            result.walkover_winner = node.winner
        else:
            if not result.home_pair_result:
                result.home_pair_result = orm.result.HomePairResult(
                    doubles_pair=home_pair, doubles_result=result
                )
            if not result.away_pair_result:
                result.away_pair_result = orm.result.AwayPairResult(
                    doubles_pair=away_pair, doubles_result=result
                )
            update_orm_doubles_result(result, node)
        self.session.add(result)
        return result

    @visit.register
    def visit_player(
        self,
        node: common_data.Player,
        **kwargs
    ) -> orm.Player:
        url = "/".join(node.url.rsplit("/", 2)[1:])
        player = orm.Player.one_or_none(
            url=url) or orm.Player(name=node.name, url=url)
        self.session.add(player)
        return player

    @visit.register
    def visit_pair(
        self,
        node: common_data.DoublesPair,
        **kwargs
    ) -> orm.DoublesPair | None:
        if node.first and node.second:
            pair = orm.DoublesPair.from_players(
                self.visit(node.first), self.visit(node.second))
            self.session.add(pair)
            return pair
        return None
