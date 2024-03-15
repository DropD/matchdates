import dataclasses
import enum
from typing import Iterator, Optional

import pendulum
import scrapy

from . import settings


SETTINGS = settings.SETTINGS["crawling"]


class Side(enum.IntEnum):
    HOME: enum.auto()
    AWAY: enum.auto()


@dataclasses.dataclass
class Player:
    name: str
    url: str


@dataclasses.dataclass
class Set:
    home_points: int
    away_points: int
    retired: Optional[Side] = None

    def __post_init__(self):
        winning_score = max([self.home_points, self.away_points])
        losing_score = min([self.home_points, self.away_points])
        difference = winning_score - losing_score
        if winning_score > 30:
            raise ValueError("A set of Badminton can not go to more than 30 points!")
        elif winning_score > 21 and difference > 2:
            raise ValueError(f"{self.home_points} : {self.away_points} is not a valid score!")
        elif 30 > winning_score > 21 and difference < 2:
            raise ValueError(f"{self.home_points} : {self.away_points} is not a valid score!")
        elif winning_score < 21 and not self.retired:
            raise ValueError(f"{self.home_points} : {self.away_points} is not a valid score if neither player retired.")
    
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
    walkover: Optional[Side] = None


@dataclasses.dataclass
class DoublesResult:
    home_pair: DoublesPair
    away_pair: DoublesPair
    set_1: Set
    set_2: Optional[Set]
    set_3: Optional[Set]
    walkover: Optional[Side] = None


@dataclasses.dataclass
class TeamMatchResult:
    mens_singles_1: SinglesResult
    mens_singles_2: SinglesResult
    mens_singles_3: SinglesResult
    mens_doubles: DoublesResult
    womens_singles: SinglesResult
    womens_doubles: DoublesResult
    mixed_doubles: DoublesResult
    walkover: Optional[Side] = None


class MatchResultSpider(scrapy.Spider):
    name = "matchdatespider"
    allowed_domains = [SETTINGS["domain"]]
    start_urls = []
    cookies = SETTINGS["cookies"]
    inspect_counter = 0

    def __init__(self, matchnrs: Optional[list[int]] = None):
        self.start_urls = [
            f"https://www.{SETTINGS['domain']}/league/{SETTINGS['league_uuid']}/draw/{i}"
            for i in matchnrs or []
        ]

    def start_requests(self) -> Iterator[scrapy.http.Request]:
        for url in self.start_urls:
            yield scrapy.http.Request(url, cookies=self.cookies, callback=self.parse_matchdetail)

    def parse_matchdetail(
            self,
            response: scrapy.http.Response,
        ) -> Iterator[TeamMatchResult]:
        raw_location_lines = (
            response.css(".page-content__sidebar .module__content")
            .xpath("*//text()").getall()
        )
        location_lines = [i.strip() for i in raw_location_lines if i.strip() and i.strip() != "Route"]
        matchdate.location = Location(location_lines[0], "\n".join(location_lines[1:]))
        event_result_elements = response.css(".match-group__item")
        event_elements_map = {}
        from scrapy.shell import inspect_response
        inspect_response(response, self)
        for event_element in event_result_elements:
            event_name = event_element.css(".match__header-title-item").xpath("*//text()").get().strip()
            event_elements_map[event_name] = event_element.css(".match__body")

        if event_elements_map:
            results = {}
            ms1_player_elements = event_elements_map["HE1"].css(".match__row-title-value-content")
            ms1_players = []
            for player_element in ms1_player_elements:
                ms1_players.append(
                    Player(
                        name=player_element.xpath("*//text()").get().strip(),
                        url=player_element.css("a::attr('href')").get()
                    )
                )
            ms1_set_elements = event_elements_map["HE1"].css(".match__result > .points")
            ms1_sets = []
            for set_element in ms1_set_elements:
                points = set_element.xpath("*//text()").getall()
                ms1_sets.append(
                    Set(
                        home_points = int(points[0].strip()),
                        away_points = int(points[1].strip()),
                    )
                )
            results["mens_singles_1"] = SinglesResult(
                home_player=ms1_players[0],
                away_player=ms1_players[1],
                set_1=ms1_sets[0],
                set_2=ms1_sets[1],
                set_3=ms1_sets[2] if len(ms1_sets) > 2 else None,
            ) 
        else:
            yield TeamMatchResult(
                **results
            )
