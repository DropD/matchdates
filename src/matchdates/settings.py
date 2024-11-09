import pathlib

import toml


def get_settings_file() -> pathlib.Path:
    name = "mada.toml"
    config_dir_order = [
        pathlib.Path("."),  # workdir
        pathlib.Path("~/.config/mada").expanduser(),  # config dir
        pathlib.Path(__file__).parent.parent,  # repo root
    ]
    for dir in config_dir_order:
        settings_file = dir / name
        if settings_file.exists():
            return settings_file
    raise FileNotFoundError("No config file found.")


def get_crawl_datadir(settings: dict) -> pathlib.Path:
    datadir = pathlib.Path(settings["crawling"]["datadir"]).expanduser().absolute()
    if not datadir.exists():
        datadir.mkdir()
    return datadir


SETTINGS = toml.load(get_settings_file())

# scrapy setting
BOT_NAME = "mada"
SPIDER_MODULES = ["matchdates.datespider", "matchdates.marespider"]
HTTPCACHE_ENABLED = True
LOG_LEVEL = "INFO"
