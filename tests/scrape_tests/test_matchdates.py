import json
import pathlib

import cattrs
import pendulum

from matchdates import common_data as cd

from .conftest import Example


def load_match_date(data_file: pathlib.Path) -> cd.MatchDate:
    data = json.load(data_file.open())
    return cattrs.structure(next(iter(data)), cd.MatchDate)


def test_common(example: Example, scraped: pathlib.Path):
    _ = load_match_date(scraped / example.date_file_name)


def test_standard_ul(standard_ul: Example, scraped: pathlib.Path):
    testee = load_match_date(scraped / standard_ul.date_file_name)
    assert testee.season.name == "Swiss Leagues 2024-25"
    assert testee.season.start_date == pendulum.Date(year=2024, month=8, day=1)
    assert testee.season.end_date == pendulum.Date(year=2025, month=5, day=31)
