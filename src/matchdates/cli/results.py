from __future__ import annotations

import json
import pathlib

import cattrs
import click
import click_spinner
import pendulum
from scrapy import crawler

from matchdates import common_data, marespider, orm, settings, data2orm
from .main import main
from .reload import latest_datafile, datafiles_outdated
from . import param_types


@main.group("results")
def results() -> None:
    """Work with match results."""
    ...


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
@ click.option("--all", is_flag=True, default=False)
@ click.option("--allow-rescrape/--no-allow-rescrape", default=False)
@ click.pass_context
def load_sqlite(ctx: click.Context, matches: list[orm.MatchDate], all: bool, allow_rescrape: bool) -> None:
    with orm.db.get_session() as session:
        if not matches:
            if all:
                matches = orm.MatchDate.all()
            else:
                matches = orm.MatchDate.filter(season=orm.Season.current())
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
            url_parts = result.url.split("/")
            season_url = "/".join(url_parts[-4:-2])
            matchdate_url = "/".join(url_parts[-2:])
            click.secho(f"found result for: {matchdate_url}", fg="red")
            season = orm.Season.one(url=season_url)
            matchdate = orm.MatchDate.one(url=matchdate_url, season=season)
            data2orm.results.ResultToOrm(
                session=session, matchdate=matchdate).visit(result)


@ results.command("show")
@ click.argument("match", type=param_types.match.Match())
@ click.pass_context
def show(ctx: click.Context, match: orm.MatchDate) -> None:
    result = orm.MatchResult.one(match_date=match)
    if not result:
        click.echo("No result found.")
        ctx.exit()
    click.echo(result.render())
