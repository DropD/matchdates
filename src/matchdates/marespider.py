import collections
import dataclasses
import enum
import re
from typing import Iterator, Optional

import scrapy

from . import settings


SETTINGS = settings.SETTINGS["crawling"]


class Side(enum.StrEnum):
    HOME = enum.auto()
    AWAY = enum.auto()


@dataclasses.dataclass
class Player:
    name: str
    url: str


@dataclasses.dataclass
class Set:
    home_points: int
    away_points: int
    retired: Optional[Side] = None

    # def __post_init__(self):
    #     winning_score = max([self.home_points, self.away_points])
    #     losing_score = min([self.home_points, self.away_points])
    #     difference = winning_score - losing_score
    #     if winning_score > 30:
    #         raise ValueError("A set of Badminton can not go to more than 30 points!")
    #     elif winning_score > 21 and difference > 2:
    #         raise ValueError(f"{self.home_points} : {self.away_points} is not a valid score!")
    #     elif 30 > winning_score > 21 and difference < 2:
    #         raise ValueError(f"{self.home_points} : {self.away_points} is not a valid score!")
    #     elif winning_score < 21 and not self.retired:
    #         raise ValueError(f"{self.home_points} : {self.away_points} is not a valid score if neither player retired.")

    @property
    def winner(self) -> Side:
        match self.retired:
            case Side.HOME:
                return Side.AWAY
            case Side.AWAY:
                return Side.HOME
            case _:
                ...

        if self.home_points > self.away_points:
            return Side.HOME
        else:
            return Side.AWAY

    def __str__(self) -> str:
        match self.retired:
            case Side.HOME:
                return f"{self.home_points} (ret.) : {self.away_points}"
            case Side.AWAY:
                return f"{self.home_points} : {self.away_points} (ret.)"
            case _:
                return f"{self.home_points} : {self.away_points}"


@dataclasses.dataclass
class DoublesPair:
    first: Player
    second: Player

    def __iter__(self):
        yield self.first
        yield self.second


@dataclasses.dataclass
class SinglesResult:
    home_player: Player
    away_player: Player
    set_1: Set
    set_2: Optional[Set]
    set_3: Optional[Set]
    winner: Side


@dataclasses.dataclass
class DoublesResult:
    home_pair: DoublesPair
    away_pair: DoublesPair
    set_1: Set
    set_2: Optional[Set]
    set_3: Optional[Set]
    winner: Side


@dataclasses.dataclass
class TeamMatchResult:
    mens_singles_1: SinglesResult
    mens_singles_2: SinglesResult
    mens_singles_3: SinglesResult
    mens_doubles: DoublesResult
    womens_singles: SinglesResult
    womens_doubles: DoublesResult
    mixed_doubles: DoublesResult
    winner: Side
    url: str


@dataclasses.dataclass
class SeniorMatchResult:
    mens_doubles: DoublesResult
    womens_doubles: DoublesResult
    mixed_doubles_1: DoublesResult
    mixed_doubles_2: DoublesResult
    winner: Side | None
    url: str


class MatchResultSpider(scrapy.Spider):
    name = "matchresultsspider"
    allowed_domains = [SETTINGS["domain"]]
    start_urls = []
    cookies = SETTINGS["cookies"]
    # cookies = None
    inspect_counter = 0
    event_name_map = {
        "HE1": "mens_singles_1",
        "HE2": "mens_singles_2",
        "HE3": "mens_singles_3",
        "HD1": "mens_doubles",
        "Men's Doubles1": "mens_doubles",
        "DE1": "womens_singles",
        "DD1": "womens_doubles",
        "Women's Doubles1": "womens_doubles",
        "GD1": "mixed_doubles",
        "GD2": "mixed_doubles_2",
    }

    def __init__(self, matchnrs: Optional[list[int]] = None, urls: Optional[list[str]] = None):
        self.start_urls = [
            f"https://www.{SETTINGS['domain']}/league/{SETTINGS['league_uuid']}/team-match/{i}"
            for i in matchnrs or []
        ] + (urls or [])

    def start_requests(self) -> Iterator[scrapy.http.Request]:
        for url in self.start_urls:
            cookies = self.cookies
            if url.startswith("file:"):
                cookies = None
            yield scrapy.http.Request(url, cookies=cookies, callback=self.parse_matchdetail)

    def parse_matchdetail(
        self,
        response: scrapy.http.Response,
    ) -> Iterator[TeamMatchResult]:
        events = response.css(".match-group__item")

        event_results = {self.event_name(
            event): self.event_details(event) for event in events}
        results = {
            k: self.details_to_singles_res(v)
            for k, v in event_results.items()
            if re.match(r".*singles.*", k)
        } | {
            k: self.details_to_doubles_res(v)
            for k, v in event_results.items()
            if re.match(r".*doubles.*", k)
        }

        wins = collections.Counter(r.winner for r in results.values())
        url = response.url.replace(
            f"https://www.{self.allowed_domains[0]}", "")

        print(url)

        if len(results) == 4:
            results["mixed_doubles_1"] = results.pop("mixed_doubles")
            winner = Side.HOME if wins[Side.HOME] > 2 else None
            winner = Side.AWAY if wins[Side.AWAY] > 2 else None
            return SeniorMatchResult(
                **results,
                winner=winner,
                url=url
            )
        return TeamMatchResult(
            **results,
            winner=max(wins, key=lambda s: wins[s]),
            url=url,
        )

    def details_to_singles_res(self, details: dict[str, list[Player] | list[Set]]) -> SinglesResult:
        score = {"set_1": None, "set_2": None, "set_3": None}
        for i, set_result in enumerate(details["sets"]):
            score[f"set_{i + 1}"] = set_result

        return SinglesResult(
            home_player=details["home_players"][0] if details["home_players"] else None,
            away_player=details["away_players"][0] if details["away_players"] else None,
            winner=details["winner"],
            **score,
        )

    def details_to_doubles_res(self, details: dict[str, list[Player] | list[Set]]) -> DoublesResult:
        score = {"set_1": None, "set_2": None, "set_3": None}
        for i, set_result in enumerate(details["sets"]):
            score[f"set_{i + 1}"] = set_result

        return DoublesResult(
            home_pair=DoublesPair(
                first=details["home_players"][0],
                second=details["home_players"][1],
            )
            if details["home_players"]
            else None,
            away_pair=DoublesPair(
                first=details["away_players"][0],
                second=details["away_players"][1],
            )
            if details["away_players"]
            else None,
            winner=details["winner"],
            **score,
        )

    def event_details(self, event: scrapy.Selector) -> SinglesResult | DoublesResult:
        data = event.css(".match__body")
        rows = data.css(".match__row")
        assert len(rows) == 2
        home_players = list(self.match_players(
            rows[0].css(".match__row-title-value-content")))
        away_players = list(self.match_players(
            rows[1].css(".match__row-title-value-content")))
        sets = list(self.match_sets(event.css(".match__result > .points")))

        winner = None
        if "has-won" in rows[0].xpath("attribute::class").get().split(" "):
            winner = Side.HOME
        elif "has-won" in rows[1].xpath("attribute::class").get().split(" "):
            winner = Side.AWAY
        assert winner

        # winning_players = list(self.match_players(data.css(".math__row .has-won > .match__row-title-value-content")))

        return {
            "home_players": home_players,
            "away_players": away_players,
            "sets": sets,
            "winner": winner,
        }

    def match_sets(self, sets: list[scrapy.Selector]) -> Iterator[Set]:
        for set in sets:
            points = set.xpath("*//text()").getall()
            assert len(points) == 2
            yield Set(home_points=int(points[0].strip()), away_points=int(points[1].strip()))

    def match_players(self, players: list[scrapy.Selector]) -> Iterator[Player]:
        for player in players:
            yield Player(
                name=player.xpath("*//text()").get().strip(),
                url=player.css("a::attr('href')").get(),
            )

    def event_name(self, event: scrapy.Selector) -> str:
        raw_event_name = event.css(
            ".match__header-title-item").xpath("*//text()").get().strip()
        return self.event_name_map[raw_event_name]
