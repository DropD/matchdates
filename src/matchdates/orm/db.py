import sqlalchemy as sqla
import sqlalchemy.orm

from matchdates import settings


SETTINGS = settings.SETTINGS["database"]


def get_db() -> sqla.Engine:
    return sqla.create_engine(f"sqlite:///{SETTINGS['sqlite_path']}")
