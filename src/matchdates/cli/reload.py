import click

from .main import main


@main.command("reload")
@click.option("--allow-rescrape/--no-allow-rescrape", default=True)
def reload(allow_rescrape):
    """Grab the dates from online and update the db."""
    import json
    import pathlib

    from . import datespider
    from scrapy import crawler

    datafiles = [
        i for i in pathlib.Path().iterdir() if i.stem.startswith("matchdates")
    ]
    datafiles.sort(key=lambda p: p.stem.split("-")[1])
    latest_date = pendulum.from_timestamp(int(datafiles[-1].stem.split("-")[1]))
    current_dates = datafiles[-1]
    click.echo(f"latest data from {latest_date}")
    if (pendulum.now() - latest_date).total_minutes() >= 10 and allow_rescrape:
        click.echo("recrawling data")
        current_dates = pathlib.Path(f"matchdates-{pendulum.now().int_timestamp}.json")

        process = crawler.CrawlerProcess(
            settings={
                "FEEDS": {
                    str(current_dates): {"format": "json"}
                }
            }
        )
        process.crawl(datespider.MatchDateSpider)
        process.start()
    else:
        click.echo("using existing data.")

    click.echo("loading crawled data")
    data = json.loads(current_dates.read_text())

    click.echo("updating database")

    for item in data:
        loc_data = item.pop("location")
        location_result = models.load_location_from_upstream(**loc_data)
        match location_result.status:
            case models.DocumentFromDataStatus.CHANGED:
                click.echo(f"Location address change: {location_result.location.name}")
                click.echo(textwrap.indent("\n".join(location_result.diff), INDENT))
            case models.DocumentFromDataStatus.NEW:
                click.echo(f"New Location found: {location_result.location.name}")
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
                            INDENT
                        )
                    )
                    click.echo(
                        textwrap.indent(
                            f"New Date: {match_result.archive_entry.date}",
                            INDENT
                        )
                    )
                if models.MatchDateChangeReason.LOCATION in match_result.change_reasons:
                    click.echo("Location Change detected:")
                    click.echo(
                        textwrap.indent(
                            str(match_result.match_date),
                            INDENT
                        )
                    )
                    click.echo(
                        textwrap.indent(
                            f"New Location: {match_result.archive_entry.location.fetch().name}",
                            INDENT
                        )
                    )
