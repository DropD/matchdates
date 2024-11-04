import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped


class Base(sqla.orm.MappedAsDataclass, sqla.orm.DeclarativeBase):
    """Base ORM Model."""


class IDMixin(sqla.orm.MappedAsDataclass):
    """Mixin for models with an autoincremented int PK"""

    id: Mapped[int] = sqla.orm.mapped_column(
        init=False, primary_key=True, autoincrement=True)
