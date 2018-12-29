import datetime

import sqlalchemy as sa

from sqlalchemy import DateTime, processors
from sqlalchemy.dialects.sqlite import DATETIME as DATETIME_


def now() -> datetime.datetime:
    """Get the current time as timezone-aware UTC timestamp."""
    return datetime.datetime.now(datetime.timezone.utc)


class SQLITEDATETIME(DATETIME_):
    """Timezone aware datetime support for SQLite.

    This is implementation used for UTCDateTime.
    """

    @staticmethod
    def process(value):
        dt = processors.str_to_datetime(value)
        if dt:
            # Returns naive datetime, force it to UTC
            return dt.replace(tzinfo=datetime.timezone.utc)
        return dt

    def result_processor(self, dialect, coltype):
        return SQLITEDATETIME.process


class UTCDateTime(DateTime):
    """An SQLAlchemy DateTime column that explicitly uses timezone aware dates and only accepts UTC."""

    def __init__(self, *args, **kwargs):
        # If there is an explicit timezone we accept UTC only
        if "timezone" in kwargs:
            assert kwargs["timezone"] in (datetime.timezone.utc, True)

        kwargs = kwargs.copy()
        kwargs["timezone"] = True
        super(UTCDateTime, self).__init__(**kwargs)

    def _dialect_info(self, dialect):
        if dialect.name == "sqlite":
            # Becase SQLite does not support datetimes, we need to explicitly tell here to use our super duper DATETIME() hack subclass that hacks in timezone
            return {"impl": SQLITEDATETIME()}
        else:
            return super(UTCDateTime, self)._dialect_info(dialect)


class TimeStampedBaseModel:
    """
    Base model with UUID as PK and have create & update timestamps
    """
    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    created_at = sa.Column(UTCDateTime, default=now)
    updated_at = sa.Column(UTCDateTime, onupdate=now)

