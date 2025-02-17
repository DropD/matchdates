from __future__ import annotations

import json
import pathlib
import tempfile
from typing import Callable, Optional

import cattrs
import click
import click_spinner
import pendulum
from scrapy import crawler

from matchdates import common_data, date_utils, models, marespider, orm, settings
from .main import main
from .reload import latest_datafile, datafiles_outdated
from . import param_types


@main.group("results")
def results() -> None:
    """Work with match results."""
    ...


def make_player(player_dict: Optional[dict[str, str]]) -> Optional[models.Player]:
    if player_dict:
        player = models.Player(**player_dict)
        if existing := models.Player.find_one({"url": player.url}):
            player = existing
        else:
            player.commit()
        return player
    return None


def make_player_sql(player: Optional[common_data.Player]) -> Optional[orm.Player]:
    if player:
        session = orm.db.get_session()
        url = "/".join(player.url.rsplit("/", 2)[1:])
        if existing := orm.Player.one_or_none(url=url):
            session.add(existing)
            return existing
        else:
            player = orm.Player(
                name=player.name,
                url=url
            )
            session.add(player)
            session.commit()
            return player
    return None


def make_pair(
    first: models.Player | None, second: models.Player | None
) -> Optional[models.DoublesPair]:
    if first and second:
        alphabetic = sorted([first, second], key=lambda p: p.name)
        pair = models.DoublesPair(first=alphabetic[0], second=alphabetic[1])
        if existing := models.DoublesPair.find_one(
            {"first": pair.first.fetch(), "second": pair.second.fetch()}
        ):
            pair = existing
        else:
            pair.commit()
        return pair
    return None


def make_pair_sql(
    first: orm.Player | None, second: orm.Player | None
) -> Optional[orm.DoublesPair]:
    if first and second:
        return orm.DoublesPair.from_players(first, second)
    return None


def make_singles_result(singles_match: dict[str, dict | int]) -> models.SinglesResult:
    home_player = make_player(singles_match["home_player"])
    away_player = make_player(singles_match["away_player"])
    s1, s2, s3 = singles_match["set_1"], singles_match["set_2"], singles_match["set_3"]
    if s1:
        s1.pop("retired")
    if s2:
        s2.pop("retired")
    if s3:
        s3.pop("retired")
    return models.SinglesResult(
        home_player=home_player,
        away_player=away_player,
        set_1=models.Set(**s1) if s1 else None,
        set_2=models.Set(**s2) if s2 else None,
        set_3=models.Set(**s3) if s3 else None,
        home_won=bool(singles_match["winner"] == 1),
    )


def make_singles_sql(
    category: common_data.ResultCategory, singles_match: common_data.SinglesResult, match_date: orm.MatchDate
) -> models.SinglesResult:
    home_player = make_player_sql(singles_match.home_player)
    away_player = make_player_sql(singles_match.away_player)
    s1, s2, s3 = singles_match.set_1, singles_match.set_2, singles_match.set_3
    singles_result = orm.SinglesResult(
        match_date=match_date,
        category=category
    )
    if not home_player or not away_player:
        singles_result.walkover_winner = singles_match.winner
    else:
        singles_result.home_player_result = orm.result.HomePlayerResult(
            player=home_player,
            singles_result=singles_result,
            set_1_points=s1.home_points if s1 else None,
            set_2_points=s2.home_points if s2 else None,
            set_3_points=s3.home_points if s3 else None,
            win=bool(singles_match.winner == common_data.Side.HOME),
        )
        singles_result.away_player_result = orm.result.AwayPlayerResult(
            player=away_player,
            singles_result=singles_result,
            set_1_points=s1.away_points if s1 else None,
            set_2_points=s2.away_points if s2 else None,
            set_3_points=s3.away_points if s3 else None,
            win=bool(singles_match.winner == common_data.Side.AWAY),
        )
    return singles_result


def make_doubles_result(doubles_match: dict[str, dict | int]) -> models.DoublesResult:
    home_pair = None
    away_pair = None
    if doubles_match["home_pair"] and doubles_match["away_pair"]:
        home_player1 = make_player(doubles_match["home_pair"]["first"])
        home_player2 = make_player(doubles_match["home_pair"]["second"])
        away_player1 = make_player(doubles_match["away_pair"]["first"])
        away_player2 = make_player(doubles_match["away_pair"]["second"])
        home_pair = make_pair(home_player1, home_player2)
        away_pair = make_pair(away_player1, away_player2)
    s1, s2, s3 = doubles_match["set_1"], doubles_match["set_2"], doubles_match["set_3"]
    if s1:
        s1.pop("retired")
    if s2:
        s2.pop("retired")
    if s3:
        s3.pop("retired")
    return models.DoublesResult(
        home_pair=home_pair,
        away_pair=away_pair,
        set_1=models.Set(**s1) if s1 else None,
        set_2=models.Set(**s2) if s2 else None,
        set_3=models.Set(**s3) if s3 else None,
        home_won=bool(doubles_match["winner"] == 1),
    )


def make_doubles_sql(
    category: common_data.ResultCategory,
    doubles_match: common_data.DoublesResult,
    match_date: orm.MatchDate
) -> orm.result.DoublesResult:
    home_pair, away_pair = None, None
    if doubles_match.home_pair:
        home_pair = make_pair_sql(
            make_player_sql(doubles_match.home_pair.first),
            make_player_sql(doubles_match.home_pair.second)
        )
    if doubles_match.away_pair:
        away_pair = make_pair_sql(
            make_player_sql(doubles_match.away_pair.first),
            make_player_sql(doubles_match.away_pair.second)
        )
    s1 = doubles_match.set_1
    s2 = doubles_match.set_2
    s3 = doubles_match.set_3
    doubles_result = orm.result.DoublesResult(
        match_date=match_date,
        category=category
    )
    doubles_result.home_pair_result = orm.result.HomePairResult(
        doubles_pair=home_pair,
        doubles_result=doubles_result,
        set_1_points=s1.home_points if s1 else None,
        set_2_points=s2.home_points if s2 else None,
        set_3_points=s3.home_points if s3 else None,
        win=bool(doubles_match.winner == common_data.Side.HOME),
    ) if home_pair else None
    doubles_result.away_pair_result = orm.result.AwayPairResult(
        doubles_pair=away_pair,
        doubles_result=doubles_result,
        set_1_points=s1.away_points if s1 else None,
        set_2_points=s2.away_points if s2 else None,
        set_3_points=s3.away_points if s3 else None,
        win=bool(doubles_match.winner == common_data.Side.AWAY),
    ) if away_pair else None
    return doubles_result


def recrawl(matches: list[orm.MatchDate]) -> pathlib.Path:
    click.echo("recrawling data")
    matchnrs = [m.matchnr for m in matches]
    click.secho(f"scraping matches: {matchnrs}", fg="red")
    new_datafile = (
        settings.get_crawl_datadir(settings.SETTINGS)
        / f"matchresults-{pendulum.now().int_timestamp}.json"
    )
    process = crawler.CrawlerProcess(
        settings={
            "FEEDS": {str(new_datafile): {"format": "json"}},
            "LOG_LEVEL": "ERROR",
        }
    )
    process.crawl(marespider.MatchResultSpider,
                  urls=[m.full_url for m in matches])
    with click_spinner.spinner():
        process.start()
    return new_datafile


@ results.command("load")
@ click.option("-M", "--match", "matches", type=param_types.match.Match(), multiple=True)
@ click.option("--allow-rescrape/--no-allow-rescrape", default=False)
@ click.pass_context
def load(ctx: click.Context, matches: list[models.MatchDate], allow_rescrape: bool) -> None:
    if not matches:
        today = pendulum.today()
        last_season_start = date_utils.season_start(today)
        matches = list(
            models.MatchDate.find(
                {"date": {"$lt": date_utils.date_to_datetime(
                    today), "$gt": last_season_start}}
            )
        )
    known_results = models.MatchResult.find({})
    known_matchnrs = set(r.match_date.fetch().url.rsplit(
        "/", 1)[1] for r in known_results)
    requested_matchnrs = set(m.matchnr for m in matches)
    matchnrs = requested_matchnrs
    if not allow_rescrape:
        matchnrs = requested_matchnrs - known_matchnrs
    if not matchnrs:
        click.echo("Nothing to do.")
        ctx.exit()
    data = {}
    with tempfile.NamedTemporaryFile() as results_file:
        process = crawler.CrawlerProcess(
            settings={
                "FEEDS": {results_file.name: {"format": "json"}},
                "LOG_LEVEL": "INFO",
            }
        )
        process.crawl(marespider.MatchResultSpider, matchnrs=matchnrs)
        process.start()
        data = json.load(results_file)

    for result in data:
        matchdate = models.MatchDate.find_one({"url": result["url"]})
        matchresult = models.MatchResult(
            match_date=matchdate,
            mens_singles_1=make_singles_result(result["mens_singles_1"]),
            mens_singles_2=make_singles_result(result["mens_singles_2"]),
            mens_singles_3=make_singles_result(result["mens_singles_3"]),
            womens_singles=make_singles_result(result["womens_singles"]),
            mens_doubles=make_doubles_result(result["mens_doubles"]),
            womens_doubles=make_doubles_result(result["womens_doubles"]),
            mixed_doubles=make_doubles_result(result["mixed_doubles"]),
        )
        if existing := models.MatchResult.find_one({"match_date": matchdate}):
            existing.mens_singles_1 = matchresult.mens_singles_1
            existing.mens_singles_2 = matchresult.mens_singles_2
            existing.mens_singles_3 = matchresult.mens_singles_3
            existing.womens_singles = matchresult.womens_singles
            existing.mens_doubles = matchresult.mens_doubles
            existing.womens_doubles = matchresult.womens_doubles
            existing.mixed_doubles = matchresult.mixed_doubles
            existing.commit()
        else:
            if any([e.set_1 for e in list(matchresult.events)]):
                matchresult.commit()


@ results.command("load-sqlite")
@ click.option("-M", "--match", "matches", type=param_types.match.Match(), multiple=True)
@ click.option("--all", is_flag=True, default=False)
@ click.option("--allow-rescrape/--no-allow-rescrape", default=False)
@ click.pass_context
def load_sqlite(ctx: click.Context, matches: list[orm.MatchDate], all: bool, allow_rescrape: bool) -> None:
    with orm.db.get_session() as session:
        if not matches:
            if all:
                matches = orm.MatchDate.all()
            else:
                today = pendulum.today()
                last_season_start = date_utils.season_start(today)
                matches = list(
                    session.scalars(
                        orm.MatchDate.select().filter(
                            (orm.MatchDate.date_time
                             < date_utils.date_to_datetime(today))  # & (orm.MatchDate.date_time
                            # > last_season_start)
                        )
                    ).all()
                )
        datadir = settings.get_crawl_datadir(settings.SETTINGS)
        datafiles = [
            i for i in datadir.iterdir() if i.name.startswith("matchresults")
        ]
        current_datafile = latest_datafile(datafiles)
        if datafiles_outdated(datafiles) and allow_rescrape:
            current_datafile = recrawl(matches)
        else:
            click.echo("using existing data.")
        data = json.loads(current_datafile.read_text())

        # TODO: use the new common_data.results classes
        for item in data:
            result = cattrs.structure(item, common_data.TeamMatchResult)
            result_url = "/".join(result.url.split("/")[-2:])
            click.secho(f"found result for: {result_url}", fg="red")
            matchdate = orm.MatchDate.one(url=result_url)
            singles_results = [
                make_singles_sql(cat, res, matchdate) for cat, res in result.singles.items()
            ]
            singles_results = [s for s in singles_results if s is not None]
            doubles_results = [
                make_doubles_sql(cat, res, matchdate) for cat, res in result.doubles.items()
            ]
            doubles_results = [d for d in doubles_results if d is not None]
            all_results = singles_results + doubles_results

            for sr in singles_results:
                if sr.home_player and matchdate.home_team not in sr.home_player.teams:
                    sr.home_player.teams.append(matchdate.home_team)
                if sr.away_player and matchdate.away_team not in sr.away_player.teams:
                    sr.away_player.teams.append(matchdate.away_team)

            for dr in doubles_results:
                if dr.home_pair:
                    for player in dr.home_pair.players:
                        if matchdate.home_team not in player.teams:
                            player.teams.append(matchdate.home_team)
                if dr.away_pair:
                    for player in dr.away_pair.players:
                        if matchdate.away_team not in player.teams:
                            player.teams.append(matchdate.away_team)

            def side_win(side: common_data.Side) -> Callable[[common_data.DoublesResult | common_data.SinglesResult], bool]:
                def inner(result: common_data.SinglesResult | common_data.DoublesResult) -> bool:
                    return bool(result.winner is side)
                return inner
            if (winner := result.winner) is not None:
                winner = orm.result.WinningTeam.HOME if winner is common_data.Side.HOME else orm.result.WinningTeam.AWAY
            home_wins = sum(
                side_win(common_data.Side.HOME)(s) for s in all_results
            )
            away_wins = sum(
                side_win(common_data.Side.AWAY)(s) for s in all_results
            )
            home_points = home_wins // 2 if singles_results else home_wins
            away_points = away_wins // 2 if singles_results else away_wins
            matchresult: orm.MatchResult
            if existing := orm.MatchResult.one_or_none(match_date=matchdate):
                matchresult = existing
                matchresult.winner = winner
                matchresult.home_points = home_points
                matchresult.away_points = away_points
            else:
                matchresult = orm.MatchResult(
                    match_date=matchdate,
                    winner=winner,
                    walkover=False,
                    home_points=home_points,
                    away_points=away_points)
            session.add_all(singles_results)
            session.add_all(doubles_results)
            session.add(matchresult)
            session.commit()


@ results.command("show")
@ click.argument("match", type=param_types.match.Match())
@ click.pass_context
def show(ctx: click.Context, match: models.MatchDate) -> None:
    result = models.MatchResult.find_one({"match_date": match})
    if not result:
        click.echo("No result found.")
        ctx.exit()
    click.echo(result.render())


@ results.command("show-sqlite")
@ click.argument("match", type=param_types.match.Match())
@ click.pass_context
def show_sqlite(ctx: click.Context, match: orm.MatchDate) -> None:
    result = orm.MatchResult.one(match_date=match)
    if not result:
        click.echo("No result found.")
        ctx.exit()
    click.echo(result.render())
