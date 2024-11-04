import json
import logging
import pathlib

import click
import pendulum
import textwrap
from scrapy import crawler

from .main import main
from . import constants
from .. import datespider, models, settings


def recrawl() -> None:
    click.echo("recrawling data")
    logging.getLogger("scrapy.core.scraper").setLevel(logging.WARN)
    logging.getLogger("scrapy.core.engine").setLevel(logging.INFO)
    new_datafile = settings.get_crawl_datadir(
        settings.SETTINGS) / f"matchdates-{pendulum.now().int_timestamp}.json"

    process = crawler.CrawlerProcess(
        settings={
            "FEEDS": {
                str(new_datafile): {"format": "json"}
            },
            "LOG_LEVEL": "INFO"
        }
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
        return (pendulum.now() - latest_date).total_minutes() >= settings.SETTINGS["crawling"]["data_min_age"]


@main.command("reload")
@click.option("--allow-rescrape/--no-allow-rescrape", default=True)
def reload(allow_rescrape: bool) -> None:
    """Grab the dates from online and update the db."""

    datadir = settings.get_crawl_datadir(settings.SETTINGS)
    datafiles = [
        i for i in datadir.iterdir() if i.stem.startswith("matchdates")
    ]
    current_datafile = latest_datafile(datafiles)

    if datafiles_outdated(datafiles) and allow_rescrape:
        current_datafile = recrawl()
    else:
        click.echo("using existing data.")

    click.echo("loading crawled data")
    data = json.loads(current_datafile.read_text())

    click.echo("updating database")

    for item in data:
        loc_data = item.pop("location")
        location_result = models.load_location_from_upstream(**loc_data)
        match location_result.status:
            case models.DocumentFromDataStatus.CHANGED:
                click.echo(
                    f"Location address change: {location_result.location.name}")
                click.echo(textwrap.indent(
                    "\n".join(location_result.diff), constants.INDENT))
            case models.DocumentFromDataStatus.NEW:
                click.echo(
                    f"New Location found: {location_result.location.name}")
            case _:
                ...

        match_result = models.load_match_date_from_upstream(
            location=location_result.location,
            **item
        )

        match match_result.status:
            case models.DocumentFromDataStatus.CHANGED:
                if models.MatchDateChangeReason.DATE in match_result.change_reasons:
                    click.echo("Date Change detected:")
                    click.echo(
                        textwrap.indent(
                            str(match_result.match_date),
                            constants.INDENT
                        )
                    )
                    click.echo(
                        textwrap.indent(
                            f"Old Date: {match_result.archive_entry.date}",
                            constants.INDENT
                        )
                    )
                if models.MatchDateChangeReason.LOCATION in match_result.change_reasons:
                    click.echo("Location Change detected:")
                    click.echo(
                        textwrap.indent(
                            str(match_result.match_date),
                            constants.INDENT
                        )
                    )
                    click.echo(
                        textwrap.indent(
                            f"Old Location: {match_result.archive_entry.location.fetch().name}",
                            constants.INDENT
                        )
                    )
