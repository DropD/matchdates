import dataclasses
from typing import Iterator, Optional

import pendulum
import scrapy

from . import settings


SETTINGS = settings.SETTINGS["crawling"]


@dataclasses.dataclass
class Location:
    name: str
    address: str


@dataclasses.dataclass
class MatchDate:
    date: pendulum.DateTime
    home_team: str
    away_team: str
    url: str
    location: Optional[Location] = None


class MatchDateSpider(scrapy.Spider):
    name = "matchdatespider"
    allowed_domains = [SETTINGS["domain"]]
    start_urls = [
        f"https://www.{SETTINGS['domain']}/league/{SETTINGS['league_uuid']}/draw/{i}"
        for i in SETTINGS["draws"]
    ]
    cookies = SETTINGS["cookies"]
    inspect_counter = 0

    def start_requests(self) -> Iterator[scrapy.http.Request]:
        for url in self.start_urls:
            yield scrapy.http.Request(url, cookies=self.cookies, callback=self.parse_draw)

    def parse_draw(self, response: scrapy.http.Response) -> Iterator[MatchDate]:
        for matchitem in response.css(".match-group__item"):
            item = MatchDate(
                date=pendulum.DateTime.fromisoformat(
                    matchitem.css("time::attr('datetime')").get()
                ),
                home_team=matchitem.css(".is-team-1").xpath("*//text()").get().strip(),
                away_team=matchitem.css(".is-team-2").xpath("*//text()").get().strip(),
                url=matchitem.css("a.team-match__wrapper::attr('href')").get(),
            )
            yield response.follow(
                item.url,
                callback=self.parse_matchdetail,
                cookies=self.cookies,
                cb_kwargs={"matchdate": item}
            )

    def parse_matchdetail(
            self,
            response: scrapy.http.Response,
            matchdate: MatchDate
        ) -> Iterator[MatchDate]:
        raw_location_lines = (
            response.css(".page-content__sidebar .module__content")
            .xpath("*//text()").getall()
        )
        location_lines = [i.strip() for i in raw_location_lines if i.strip() and i.strip() != "Route"]
        matchdate.location = Location(location_lines[0], "\n".join(location_lines[1:]))
        yield matchdate
