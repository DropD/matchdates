import collections
import dataclasses
import enum
import re
from typing import Iterator, Optional

import scrapy

from . import settings
from matchdates.common_data import (
    DoublesPair, DoublesResult, Player, Set, Side, SinglesResult,
    TeamMatchResult, ResultCategory
)


SETTINGS = settings.SETTINGS["crawling"]


class MatchResultSpider(scrapy.Spider):
    name = "matchresultsspider"
    allowed_domains = [SETTINGS["domain"]]
    start_urls = []
    cookies = SETTINGS["cookies"]
    # cookies = None
    inspect_counter = 0
    event_cat_map = {
        "HE1": ResultCategory.HE1,
        "HE2": ResultCategory.HE2,
        "HE3": ResultCategory.HE3,
        "HD1": ResultCategory.HD1,
        "HD2": ResultCategory.HD2,
        "Men's Doubles1": ResultCategory.HD1,
        "Men's Doubles2": ResultCategory.HD2,
        "DE1": ResultCategory.DE1,
        "DD1": ResultCategory.DD1,
        "Women's Doubles1": ResultCategory.DD1,
        "GD1": ResultCategory.MX1,
        "GD2": ResultCategory.MX2,
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
        singles = {
            k: self.details_to_singles_res(v)
            for k, v in event_results.items()
            if k in ResultCategory.singles_categories
        }
        doubles = {
            k: self.details_to_doubles_res(v)
            for k, v in event_results.items()
            if k in ResultCategory.doubles_categories
        }

        wins = collections.Counter(
            r.winner for r in (singles | doubles).values())
        url = response.url.replace(
            f"https://www.{self.allowed_domains[0]}", "")

        winner = Side.NEITHER
        if not wins[Side.HOME] == wins[Side.AWAY]:
            winner = max(wins, key=lambda s: wins[s])
        yield TeamMatchResult(
            singles=singles,
            doubles=doubles,
            winner=winner,
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

        winner = Side.NEITHER
        if "has-won" in rows[0].xpath("attribute::class").get().split(" "):
            winner = Side.HOME
        elif "has-won" in rows[1].xpath("attribute::class").get().split(" "):
            winner = Side.AWAY

        retired = Side.NEITHER
        if "Retired" in rows[0].xpath("*//text()").get():
            retired = Side.HOME
        elif "Retired" in rows[1].xpath("*//text()").get():
            retired = Side.AWAY

        assert any([
            len(home_players) > 0,
            len(away_players) > 0,
            len(sets) > 0,
            winner
        ])
        # winning_players = list(self.match_players(data.css(".math__row .has-won > .match__row-title-value-content")))

        return {
            "home_players": home_players,
            "away_players": away_players,
            "sets": sets,
            "winner": winner,
            "retired": retired,
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

    def event_name(self, event: scrapy.Selector) -> ResultCategory:
        raw_event_name = event.css(
            ".match__header-title-item").xpath("*//text()").get().strip()
        return self.event_cat_map[raw_event_name]
