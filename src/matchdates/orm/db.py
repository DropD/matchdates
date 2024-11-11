import sqlalchemy as sqla
import sqlalchemy.orm

from matchdates import settings


SETTINGS = settings.SETTINGS["database"]
__ENGINE: sqla.Engine | None = None
__SESSION: sqla.orm.Session | None = None


def get_db() -> sqla.Engine:
    global __ENGINE
    if __ENGINE is None:
        __ENGINE = sqla.create_engine(f"sqlite:///{SETTINGS['sqlite_path']}")
    return __ENGINE


def get_session() -> sqla.orm.Session:
    global __SESSION
    if __SESSION is None:
        __SESSION = sqla.orm.Session(get_db())
    return __SESSION
