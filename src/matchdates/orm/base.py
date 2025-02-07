from typing import Any, Self, Iterator

import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped

from . import db


class Base(sqla.orm.MappedAsDataclass, sqla.orm.DeclarativeBase):
    """Base ORM Model."""

    metadata = sqla.MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    @classmethod
    def select(cls: type[Self], *other_entities: Any) -> sqla.Select:
        if other_entities:
            return sqla.select(cls, *other_entities)
        return sqla.select(cls)

    @classmethod
    def all(cls: type[Self]) -> Iterator[Self]:
        return db.get_session().scalars(cls.select()).all()

    @classmethod
    def get(cls: type[Self], id: Any) -> Self:
        return db.get_session().session.get(cls, id)

    @classmethod
    def one(cls: type[Self], **filters: Any) -> Self:
        return db.get_session().scalars(cls.select().filter_by(**filters)).one()

    @classmethod
    def one_or_none(cls: type[Self], **filters: Any) -> Self | None:
        return db.get_session().scalars(cls.select().filter_by(**filters)).one_or_none()


class IDMixin(sqla.orm.MappedAsDataclass):
    """Mixin for models with an autoincremented int PK"""

    id: Mapped[int] = sqla.orm.mapped_column(
        init=False, primary_key=True, autoincrement=True)
