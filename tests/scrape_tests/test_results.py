import json
import pathlib

import cattrs
import pendulum

from matchdates import common_data, orm
from matchdates.cli import results

from .conftest import Example


def compare_winners(result: dict[str, str], reference: Example) -> None:
    results = result.singles | result.doubles
    for k, v in reference.winners.items():
        assert results[k].winner == reference.winners[k]
    assert result.winner == reference.winner


def test_winners(example: Example, scraped: pathlib.Path):
    """Check that the right winners are detected."""
    result_file = scraped / example.result_file_name
    data = json.load(result_file.open())

    assert len(data) == 1
    testee = cattrs.structure(next(iter(data)), common_data.TeamMatchResult)
    compare_winners(testee, example)


def test_player_retired(retired_player: Example, scraped: pathlib.Path):
    """Check that the away mixed pair is recorded as retired."""
    result_file = scraped / retired_player.result_file_name
    data = json.load(result_file.open())

    testee = cattrs.structure(next(iter(data)), common_data.TeamMatchResult)

    testee.doubles[common_data.ResultCategory.MX1].retired == retired_player.players_retired[common_data.ResultCategory.MX1]


def test_make_player_sql(example: Example, scraped: pathlib.Path, db_session):
    """Check that creating players from the scraped data does not raise errors."""
    result_file = scraped / example.result_file_name
    data = json.load(result_file.open())
    testee = next(iter(data))

    for key, value in testee.items():
        if isinstance(value, dict):
            if player := value.get("home_player", None):
                results.make_player_sql(player)
            if isinstance(pair := value.get("home_pair", None), dict):
                results.make_player_sql(pair["first"])
                results.make_player_sql(pair["second"])
            if player := value.get("away_player", None):
                results.make_player_sql(player)
            if isinstance(pair := value.get("away_pair", None), dict):
                results.make_player_sql(pair["first"])
                results.make_player_sql(pair["second"])


def test_make_pair_sql(example: Example, scraped: pathlib.Path, db_session):
    """Check that creating pairs from the scraped data does not raise errors."""
    result_file = scraped / example.result_file_name
    data = json.load(result_file.open())
    testee = next(iter(data))

    for key, value in testee.items():
        if isinstance(value, dict):
            if isinstance(pair := value.get("home_pair", None), dict):
                results.make_pair_sql(
                    results.make_player_sql(pair["first"]),
                    results.make_player_sql(pair["second"])
                )
            if isinstance(pair := value.get("away_pair", None), dict):
                results.make_pair_sql(
                    results.make_player_sql(pair["first"]),
                    results.make_player_sql(pair["second"])
                )


def test_make_singles_sql(example: Example, scraped: pathlib.Path, db_session):
    """Check that creating singles results does not raise erorrs."""
    result_file = scraped / example.result_file_name
    data = json.load(result_file.open())
    testee = next(iter(data))

    for key, value in testee.items():
        if isinstance(value, dict) and "home_player" in value:
            url = "/".join(testee["url"].split("/")[-2:])
            matchdate = orm.MatchDate(url=url, date_time=pendulum.now())
            results.make_singles_sql(
                common_data.ResultCategory.HE1, value, matchdate
            )


def test_make_doubles_sql(example: Example, scraped: pathlib.Path, db_session):
    """Check that creating doubles results does not raise errors."""
    result_file = scraped / example.result_file_name
    data = json.load(result_file.open())
    testee = next(iter(data))

    for key, value in testee.items():
        if isinstance(value, dict) and "home_pair" in value:
            url = "/".join(testee["url"].split("/")[-2:])
            matchdate = orm.MatchDate(url=url, date_time=pendulum.now())
            results.make_doubles_sql(
                common_data.ResultCategory.HD1, value, matchdate
            )
