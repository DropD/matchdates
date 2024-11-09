
import sqlalchemy as sqla
import sqlalchemy.orm
from sqlalchemy.orm import Mapped


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


class IDMixin(sqla.orm.MappedAsDataclass):
    """Mixin for models with an autoincremented int PK"""

    id: Mapped[int] = sqla.orm.mapped_column(init=False, primary_key=True, autoincrement=True)
