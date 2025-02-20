import json
import logging
import pathlib

import cattrs
import click
import pendulum
import textwrap
from scrapy import crawler

from .. import common_data as cd, data2orm, datespider, settings
from .. import orm
from .main import main
from . import constants


def recrawl() -> pathlib.Path:
    click.echo("recrawling data")
    logging.getLogger("scrapy.core.scraper").setLevel(logging.WARN)
    logging.getLogger("scrapy.core.engine").setLevel(logging.INFO)
    new_datafile = (
        settings.get_crawl_datadir(settings.SETTINGS)
        / f"matchdates-{pendulum.now().int_timestamp}.json"
    )

    process = crawler.CrawlerProcess(
        settings={
            "FEEDS": {str(new_datafile): {"format": "json"}}, "LOG_LEVEL": "INFO"}
    )
    process.crawl(datespider.MatchDateSpider)
    process.start()
    return new_datafile


def latest_datafile(datafiles: list[pathlib.Path]) -> pathlib.Path:
    if not datafiles:
        return None
    return sorted(datafiles, key=lambda p: p.stem.split("-")[1])[-1]


def datafiles_outdated(datafiles: list[pathlib.Path]) -> bool:
    if not datafiles:
        return True
    else:
        current_datafile = latest_datafile(datafiles)
        latest_date = pendulum.from_timestamp(
            int(current_datafile.stem.split("-")[1]))
        click.echo(f"latest data from {latest_date}")
        return (pendulum.now() - latest_date).total_minutes() >= settings.SETTINGS["crawling"][
            "data_min_age"
        ]


@main.command("reload")
@click.option("--allow-rescrape/--no-allow-rescrape", default=True)
def reload(allow_rescrape: bool) -> None:
    """Grab the dates from online and update the db."""
    datadir = settings.get_crawl_datadir(settings.SETTINGS)
    datafiles = [i for i in datadir.iterdir(
    ) if i.stem.startswith("matchdates")]
    current_datafile = latest_datafile(datafiles)

    if datafiles_outdated(datafiles) and allow_rescrape:
        current_datafile = recrawl()
    else:
        click.echo("using existing data.")

    click.echo("loading crawled data")
    data = json.loads(current_datafile.read_text())

    click.echo("updating database")

    converter = data2orm.matchdate.MatchdateToOrm(session=orm.db.get_session())
    for item in data:
        matchitem = cattrs.structure(item, cd.MatchDate)
        matchdate = converter.visit(matchitem)
        last_change = next(
            iter(reversed(matchdate.changelog))
        ) if matchdate.changelog else None
        if last_change and (
                pendulum.now() - last_change.archived_date_time
        ).in_seconds() < 5:
            if last_change.location != matchdate.location:
                click.echo("Location Change detected:")
                click.echo(textwrap.indent(
                    str(matchdate.match_date), constants.INDENT))
                click.echo(
                    textwrap.indent(
                        f"Old Location: {matchdate.archive_entry.location.name}",
                        constants.INDENT,
                    )
                )
            if last_change.date_time != matchdate.date_time:
                click.echo("Date Change detected:")
                click.echo(textwrap.indent(
                    str(matchdate.match_date), constants.INDENT))
                click.echo(
                    textwrap.indent(
                        f"Old Date: {matchdate.archive_entry.date_time}", constants.INDENT
                    )
                )
