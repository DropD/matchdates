import re
from typing import Iterator

import pendulum
import scrapy

from . import common_data as cd, settings


SETTINGS = settings.SETTINGS["crawling"]


class MatchDateSpider(scrapy.Spider):
    name = "matchdatespider"
    allowed_domains = [SETTINGS["domain"]]
    start_urls = [
        f"https://www.{SETTINGS['domain']}/league/{SETTINGS['league_uuid']}/draw/{i}"
        for i in SETTINGS["draws"]
    ]
    cookies = SETTINGS["cookies"]
    inspect_counter = 0

    def __init__(self, urls: list[str] | None = None):
        self.scrape_individual_matches = False
        if urls:
            self.scrape_individual_matches = True
            self.start_urls = urls

    def start_requests(self) -> Iterator[scrapy.http.Request]:
        if self.scrape_individual_matches:
            for url in self.start_urls:
                yield scrapy.http.Request(url, cookies=self.cookies, callback=self.parse_matchdetail)
        else:
            for url in self.start_urls:
                yield scrapy.http.Request(url, cookies=self.cookies, callback=self.parse_draw)

    def parse_draw(self, response: scrapy.http.Response) -> Iterator[cd.MatchDate]:
        for matchitem in response.css(".match-group__item"):
            url = matchitem.css("a.team-match__wrapper::attr('href')").get()
            # item = cd.MatchDate(
            #     date=pendulum.DateTime.fromisoformat(
            #         matchitem.css("time::attr('datetime')").get()),
            #     home_team=matchitem.css(
            #         ".is-team-1").xpath("*//text()").get().strip(),
            #     away_team=matchitem.css(
            #         ".is-team-2").xpath("*//text()").get().strip(),
            #     url=matchitem.css("a.team-match__wrapper::attr('href')").get(),
            # )
            yield response.follow(
                url,
                callback=self.parse_matchdetail,
                cookies=self.cookies,
                # cb_kwargs={"matchdate": item},
            )

    def parse_season(self, season_item: scrapy.Selector) -> cd.Season:
        dates = season_item.xpath(
            "*//li[1]/*//text()").get().strip().split(" - ")
        date_format = "DD. MMMM YYYY"
        name = season_item.css(".nav-link__value::text").get().strip()
        years = name.rsplit(" ", 1)[1].split("-") if name else ["2024", "25"]
        years[1] = years[0][:2] + years[1]
        dates = [f"{d} {y}" for d, y in zip(dates, years, strict=True)]
        return cd.Season(
            url=season_item.css(".nav-link::attr('href')").get(),
            name=name,
            start_date=pendulum.from_format(
                dates[0], date_format, locale="de"
            ).date(),
            end_date=pendulum.from_format(
                dates[1], date_format, locale="de"
            ).date()
        )

    def parse_matchdetail(
        self, response: scrapy.http.Response  # , matchdate: cd.MatchDate
    ) -> Iterator[cd.MatchDate]:
        matchitem = response.css(".team-match-header")

        home_team_name = matchitem.css(
            ".is-team-1::attr(title)").get().strip()
        home_club_name = home_team_name
        if re.match(r"\d*", home_club_name.split(" ")[-1]):
            home_club_name = " ".join(home_club_name.split(" ")[:-1])

        away_team_name = matchitem.css(
            ".is-team-2::attr(title)").get().strip()
        away_club_name = away_team_name
        if re.match(r"\d*", away_club_name.split(" ")[-1]):
            away_club_name = " ".join(away_club_name.split(" ")[:-1])

        matchdate = cd.MatchDate(
            home_team=cd.Team(
                name=home_team_name,
                url=matchitem.css(".is-team-1 a::attr('href')").get(),
                club=cd.Club(name=home_club_name)
            ),
            away_team=cd.Team(
                name=away_team_name,
                url=matchitem.css(".is-team-2 a::attr('href')").get(),
                club=cd.Club(name=away_club_name)
            ),
            date=pendulum.instance(
                pendulum.DateTime.fromisoformat(
                    matchitem.xpath("//@datetime[1]").get()
                ),
                tz=pendulum.local_timezone()
            ),
            url=response.url
        )
        season = self.parse_season(response.css("header .media__content"))
        draw = cd.Draw(
            response.css(
                ".team-match-header .text--center a::attr('href')"
            ).get()
        )
        raw_location_lines = (
            response.css(
                ".page-content__sidebar .module__content").xpath("*//text()").getall()
        )
        location_lines = [
            i.strip() for i in raw_location_lines if i.strip() and i.strip() != "Route"
        ]
        matchdate.location = cd.Location(
            location_lines[0], "\n".join(location_lines[1:]))
        matchdate.season = season
        matchdate.draw = draw
        yield matchdate
