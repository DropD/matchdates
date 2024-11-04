import json
import tempfile
from typing import Optional

import click
import pendulum
from scrapy import crawler

from .. import models, marespider, date_utils
from .main import main
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


def make_pair(first: Optional[models.Player], second: Optional[models.Player]) -> Optional[models.DoublesPair]:
    if first and second:
        alphabetic = sorted([first, second], key=lambda p: p.name)
        pair = models.DoublesPair(first=alphabetic[0], second=alphabetic[1])
        if existing := models.DoublesPair.find_one({"first": pair.first.fetch(), "second": pair.second.fetch()}):
            pair = existing
        else:
            pair.commit()
        return pair
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
        home_won=bool(singles_match["winner"] == 1)
    )


def make_doubles_result(singles_match: dict[str, dict | int]) -> models.SinglesResult:
    home_pair = None
    away_pair = None
    if singles_match["home_pair"] and singles_match["away_pair"]:
        home_player1 = make_player(singles_match["home_pair"]["first"])
        home_player2 = make_player(singles_match["home_pair"]["second"])
        away_player1 = make_player(singles_match["away_pair"]["first"])
        away_player2 = make_player(singles_match["away_pair"]["second"])
        home_pair = make_pair(home_player1, home_player2)
        away_pair = make_pair(away_player1, away_player2)
    s1, s2, s3 = singles_match["set_1"], singles_match["set_2"], singles_match["set_3"]
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
        home_won=bool(singles_match["winner"] == 1)
    )


@results.command("load")
@click.option("-M", "--match", "matches", type=param_types.match.Match(), multiple=True)
@click.option("--allow-rescrape/--no-allow-rescrape", default=False)
@click.pass_context
def load(ctx: click.Context, matches: list[models.MatchDate], allow_rescrape: bool) -> None:
    if not matches:
        today = pendulum.today()
        last_season_start = date_utils.season_start(today)
        matches = list(models.MatchDate.find(
            {"date": {"$lt": date_utils.date_to_datetime(today), "$gt": last_season_start}}))
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
                "FEEDS": {
                    results_file.name: {"format": "json"}
                },
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


@results.command("show")
@click.argument("match", type=param_types.match.Match())
@click.pass_context
def show(ctx: click.Context, match: models.MatchDate) -> None:
    result = models.MatchResult.find_one({"match_date": match})
    if not result:
        click.echo("No result found.")
        ctx.exit()
    click.echo(result.render())
