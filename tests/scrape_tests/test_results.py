import json
import pathlib

from scrapy import crawler

from matchdates import marespider

from .conftest import Example


def compare_winners(result: dict[str, str], reference: Example) -> None:
    for k, v in reference.winners.items():
        title = k.replace(
            "he", "mens_singles_"
        ).replace(
            "de1", "womens_singles"
        ).replace(
            "hd1", "mens_doubles"
        ).replace(
            "dd1", "womens_doubles"
        ).replace(
            "xd", "mixed_doubles_"
        )
        if len(reference.winners) != 4:
            title = title.replace("mixed_doubles_1", "mixed_doubles")
        assert result[title]["winner"] == reference.winners[k]
    assert result["winner"] == reference.winner


def test_winners(example: Example, scraped: pathlib.Path):
    result_file = scraped / example.result_file_name
    data = json.load(result_file.open())

    assert len(data) == 1
    testee = next(iter(data))
    compare_winners(testee, example)
