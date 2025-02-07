import dataclasses
import json
import pathlib
from typing import Iterator

import pytest
from scrapy import crawler

from matchdates import marespider


@dataclasses.dataclass(kw_only=True)
class Example:
    filename: str
    winners: dict[str, str]
    team_points: dict[str, int]
    team_retired: str | None = None
    players_retired: dict[str, str] = dataclasses.field(default_factory=dict)
    walkovers: dict[str, str] = dataclasses.field(default_factory=dict)
    winner: str | None

    @property
    def url(self) -> str:
        path = pathlib.Path(__file__).parent / "pages" / self.filename
        return f"file://{path.absolute()}"

    @property
    def result_file_name(self) -> str:
        matchnr = self.url.replace(".html", "").split("_")[-1]
        return f"{matchnr}.json"


@pytest.fixture(scope="session")
def adjusted() -> Iterator[Example]:
    yield Example(
        filename="https___www.swiss-badminton.ch_league_4D2A187C-0855-4B4F-B106-6B6413FC17BF_team-match_7162.html",
        winners={
            "he1": "away",
            "he2": "away",
            "he3": "away",
            "de1": "away",
            "hd1": "away",
            "dd1": "away",
            "xd1": "home"
        },
        team_points={
            "home": 0,
            "away": 3
        },
        winner="away"
    )


@pytest.fixture(scope="session")
def team_retired() -> Iterator[Example]:
    yield Example(
        filename="https___www.swiss-badminton.ch_league_4D2A187C-0855-4B4F-B106-6B6413FC17BF_team-match_6006.html",
        winners={
            "he1": "home",
            "he2": "home",
            "he3": "away",
            "de1": "home",
            "hd1": "home",
            "dd1": "away",
            "xd1": "away"
        },
        team_points={
            "home": 0,
            "away": 0
        },
        team_retired="home",
        winner="home"
    )


@pytest.fixture(scope="session")
def standard_ul() -> Iterator[Example]:
    yield Example(
        filename="https___www.swiss-badminton.ch_league_4D2A187C-0855-4B4F-B106-6B6413FC17BF_team-match_7467.html",
        winners={
            "he1": "away",
            "he2": "away",
            "he3": "away",
            "de1": "away",
            "hd1": "away",
            "dd1": "home",
            "xd1": "away"
        },
        team_points={
            "home": 0,
            "away": 3
        },
        winner="away"
    )


@pytest.fixture(scope="session")
def standard_sl() -> Iterator[Example]:
    yield Example(
        filename="https___www.swiss-badminton.ch_league_4D2A187C-0855-4B4F-B106-6B6413FC17BF_team-match_8919.html",
        winners={
            "dd1": "home",
            "hd1": "away",
            "xd1": "away",
            "xd2": "home"
        },
        team_points={
            "home": 2,
            "away": 2
        },
        winner=None
    )


@pytest.fixture(scope="session")
def walkover_player() -> Iterator[Example]:
    yield Example(
        filename="https___www.swiss-badminton.ch_league_4D2A187C-0855-4B4F-B106-6B6413FC17BF_team-match_7455.html",
        winners={
            "he1": "away",
            "he2": "home",
            "he3": "home",
            "de1": "away",
            "hd1": "home",
            "dd1": "away",
            "xd1": "home"
        },
        team_points={
            "home": 2,
            "away": 1
        },
        walkovers={
            "he3": "away",
            "hd1": "away"
        },
        winner="home"
    )


@pytest.fixture(scope="session")
def retired_player() -> Iterator[Example]:
    yield Example(
        filename="https___www.swiss-badminton.ch_league_4D2A187C-0855-4B4F-B106-6B6413FC17BF_team-match_7033.html",
        winners={
            "he1": "home",
            "he2": "home",
            "he3": "home",
            "de1": "home",
            "hd1": "home",
            "dd1": "home",
            "xd1": "home"
        },
        team_points={
            "home": 3,
            "away": 0
        },
        players_retired={
            "xd1": "away"
        },
        winner="home"
    )


ALL_EXAMPLES = [
    "adjusted",
    "team_retired",
    "standard_sl",
    "standard_ul",
    "walkover_player",
    "retired_player"
]


@pytest.fixture(params=ALL_EXAMPLES, scope="session")
def example(request) -> Example:
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="session")
def scraped(
    request,
    tmp_path_factory: pathlib.Path
) -> Iterator[pathlib.Path]:
    examples = [request.getfixturevalue(example) for example in ALL_EXAMPLES]
    results_dir = tmp_path_factory.mktemp("results")
    result_file = results_dir / "results.json"
    proc = crawler.CrawlerProcess(
        settings={
            "FEEDS": {str(result_file.absolute()): {"format": "json"}},
            "LOG_LEVEL": "ERROR",
        }
    )
    proc.crawl(
        marespider.MatchResultSpider,
        urls=[
            example.url for example in examples
        ]
    )
    proc.start()
    all_data = json.load(result_file.open())
    for res in all_data:
        matchnr = res["url"].replace(".html", "").split("_")[-1]
        res_file = results_dir / f"{matchnr}.json"
        res_file.write_text(json.dumps([res]))
    yield results_dir
