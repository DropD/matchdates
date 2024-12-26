import typing
import sqlalchemy as sqla
import sqlalchemy.orm
from typing import Self

from matchdates import settings


SETTINGS = settings.SETTINGS["database"]


class DbContext:
    __stack: typing.ClassVar[list[Self]] = []

    __db_url: str
    __engine: sqla.Engine | None = None
    __session: sqla.orm.Session | None = None

    def __init__(self, db_url: str):
        self.__db_url = db_url

    @property
    def engine(self) -> sqla.Engine:
        if self.__engine is None:
            self.__engine = self.new_engine()
        return self.__engine

    @property
    def session(self) -> sqla.orm.Session:
        if self.__session is None:
            self.__session = self.new_session()
        return self.__session

    def new_engine(self) -> sqla.Engine:
        return sqla.create_engine(self.__db_url)

    def new_session(self) -> sqla.orm.Session:
        return sqla.orm.Session(self.engine)

    def close(self) -> None:
        if self.__session:
            self.__session.close()

    @classmethod
    def push(cls, db_url: str) -> Self:
        new = cls(db_url)
        cls.__stack.append(new)
        return new

    @classmethod
    def pop(cls) -> Self:
        old_top = cls.__stack.pop()
        old_top.close()
        return old_top

    @classmethod
    def top(cls) -> Self:
        if not cls.__stack:
            cls.push(f"sqlite:///{SETTINGS['sqlite_path']}")
        return cls.__stack[-1]


def current_context() -> DbContext:
    return DbContext.top()


def get_db() -> sqla.Engine:
    return current_context().engine


def get_session() -> sqla.orm.Session:
    return current_context().session
