import dataclasses
import json
import pathlib
from typing import Iterator

import pytest
from scrapy import crawler

from matchdates import common_data, marespider, datespider


@dataclasses.dataclass(kw_only=True)
class Example:
    url: str
    winners: dict[common_data.ResultCategory, common_data.Side]
    team_points: dict[common_data.Side, int]
    team_retired: common_data.Side = common_data.Side.NEITHER
    players_retired: dict[
        common_data.ResultCategory, common_data.Side
    ] = dataclasses.field(default_factory=dict)
    walkovers: dict[
        common_data.ResultCategory, common_data.Side
    ] = dataclasses.field(default_factory=dict)
    winner: common_data.Side
    #
    # @property
    # def url(self) -> str:
    #     # path = pathlib.Path(__file__).parent / "pages" / self.filename
    #     # return f"file://{path.absolute()}"
    #     return self.url

    @property
    def matchnr(self) -> str:
        return self.url.replace(".html", "").split("/")[-1]

    @property
    def result_file_name(self) -> str:
        return f"{self.matchnr}.json"

    @property
    def date_file_name(self) -> str:
        return f"matchdate-{self.matchnr}.json"


@pytest.fixture(scope="session")
def adjusted() -> Iterator[Example]:
    yield Example(
        url="https://www.swiss-badminton.ch/league/4D2A187C-0855-4B4F-B106-6B6413FC17BF/team-match/7162",
        winners={
            common_data.ResultCategory.HE1: common_data.Side.AWAY,
            common_data.ResultCategory.HE2: common_data.Side.AWAY,
            common_data.ResultCategory.HE3: common_data.Side.AWAY,
            common_data.ResultCategory.DE1: common_data.Side.AWAY,
            common_data.ResultCategory.HD1: common_data.Side.AWAY,
            common_data.ResultCategory.DD1: common_data.Side.AWAY,
            common_data.ResultCategory.MX1: common_data.Side.HOME
        },
        team_points={
            common_data.Side.HOME: 0,
            common_data.Side.AWAY: 3
        },
        winner=common_data.Side.AWAY
    )


@pytest.fixture(scope="session")
def team_retired() -> Iterator[Example]:
    yield Example(
        url="https://www.swiss-badminton.ch/league/4D2A187C-0855-4B4F-B106-6B6413FC17BF/team-match/6006",
        winners={
            common_data.ResultCategory.HE1: common_data.Side.HOME,
            common_data.ResultCategory.HE2: common_data.Side.HOME,
            common_data.ResultCategory.HE3: common_data.Side.AWAY,
            common_data.ResultCategory.DE1: common_data.Side.HOME,
            common_data.ResultCategory.HD1: common_data.Side.HOME,
            common_data.ResultCategory.DD1: common_data.Side.AWAY,
            common_data.ResultCategory.MX1: common_data.Side.AWAY
        },
        team_points={
            common_data.Side.HOME: 0,
            common_data.Side.AWAY: 0
        },
        team_retired=common_data.Side.HOME,
        winner=common_data.Side.HOME
    )


@pytest.fixture(scope="session")
def standard_ul() -> Iterator[Example]:
    yield Example(
        url="https://www.swiss-badminton.ch/league/4D2A187C-0855-4B4F-B106-6B6413FC17BF/team-match/7467",
        winners={
            common_data.ResultCategory.HE1: common_data.Side.AWAY,
            common_data.ResultCategory.HE2: common_data.Side.AWAY,
            common_data.ResultCategory.HE3: common_data.Side.AWAY,
            common_data.ResultCategory.DE1: common_data.Side.AWAY,
            common_data.ResultCategory.HD1: common_data.Side.AWAY,
            common_data.ResultCategory.DD1: common_data.Side.HOME,
            common_data.ResultCategory.MX1: common_data.Side.AWAY
        },
        team_points={
            common_data.Side.HOME: 0,
            common_data.Side.AWAY: 3
        },
        winner=common_data.Side.AWAY
    )


@pytest.fixture(scope="session")
def standard_sl() -> Iterator[Example]:
    yield Example(
        url="https://www.swiss-badminton.ch/league/4D2A187C-0855-4B4F-B106-6B6413FC17BF/team-match/8919",
        winners={
            common_data.ResultCategory.DD1: common_data.Side.HOME,
            common_data.ResultCategory.HD1: common_data.Side.AWAY,
            common_data.ResultCategory.MX1: common_data.Side.AWAY,
            common_data.ResultCategory.MX2: common_data.Side.HOME
        },
        team_points={
            common_data.Side.HOME: 2,
            common_data.Side.AWAY: 2
        },
        winner=common_data.Side.NEITHER
    )


@pytest.fixture(scope="session")
def walkover_player() -> Iterator[Example]:
    yield Example(
        url="https://www.swiss-badminton.ch/league/4D2A187C-0855-4B4F-B106-6B6413FC17BF/team-match/7455",
        winners={
            common_data.ResultCategory.HE1: common_data.Side.AWAY,
            common_data.ResultCategory.HE2: common_data.Side.HOME,
            common_data.ResultCategory.HE3: common_data.Side.HOME,
            common_data.ResultCategory.DE1: common_data.Side.AWAY,
            common_data.ResultCategory.HD1: common_data.Side.HOME,
            common_data.ResultCategory.DD1: common_data.Side.AWAY,
            common_data.ResultCategory.MX1: common_data.Side.HOME
        },
        team_points={
            common_data.Side.HOME: 2,
            common_data.Side.AWAY: 1
        },
        walkovers={
            common_data.ResultCategory.HE3: common_data.Side.AWAY,
            common_data.ResultCategory.HD1: common_data.Side.AWAY
        },
        winner=common_data.Side.HOME
    )


@pytest.fixture(scope="session")
def retired_player() -> Iterator[Example]:
    yield Example(
        url="https://www.swiss-badminton.ch/league/4D2A187C-0855-4B4F-B106-6B6413FC17BF/team-match/7033",
        winners={
            common_data.ResultCategory.HE1: common_data.Side.HOME,
            common_data.ResultCategory.HE2: common_data.Side.HOME,
            common_data.ResultCategory.HE3: common_data.Side.HOME,
            common_data.ResultCategory.DE1: common_data.Side.HOME,
            common_data.ResultCategory.HD1: common_data.Side.HOME,
            common_data.ResultCategory.DD1: common_data.Side.HOME,
            common_data.ResultCategory.MX1: common_data.Side.HOME
        },
        team_points={
            common_data.Side.HOME: 3,
            common_data.Side.AWAY: 0
        },
        players_retired={
            common_data.ResultCategory.MX1: common_data.Side.AWAY
        },
        winner=common_data.Side.HOME
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
    date_file = results_dir / "matchdates.json"
    proc = crawler.CrawlerProcess(
        settings={
            "FEEDS": {str(result_file.absolute()): {"format": "json"}},
            "HTTPCACHE_ENABLED": True,
            "LOG_LEVEL": "ERROR",
        }
    )
    proc.crawl(
        marespider.MatchResultSpider,
        urls=[
            example.url for example in examples
        ]
    )
    datespider.MatchDateSpider.custom_settings = {
        "FEEDS": {str(date_file.absolute()): {"format": "json"}}
    }
    proc.crawl(
        datespider.MatchDateSpider,
        urls=[
            example.url for example in examples
        ]
    )
    proc.start()
    all_results = json.load(result_file.open())
    for res in all_results:
        matchnr = res["url"].split("/")[-1]
        res_file = results_dir / f"{matchnr}.json"
        res_file.write_text(json.dumps([res]))

    all_matchdates = json.load(date_file.open())
    for md in all_matchdates:
        matchnr = md["url"].split("/")[-1]
        md_file = results_dir / f"matchdate-{matchnr}.json"
        md_file.write_text(json.dumps([md]))
    yield results_dir
