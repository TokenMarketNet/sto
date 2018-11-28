import datetime

import sqlalchemy as sa

from sqlalchemy import DateTime


def now() -> datetime.datetime:
    """Get the current time as timezone-aware UTC timestamp."""
    return datetime.datetime.now(datetime.timezone.utc)


class TimeStampedBaseModel:
    """
    Base model with UUID as PK and have create & update timestamps
    """
    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    created_at = sa.Column(DateTime, default=now)
    updated_at = sa.Column(DateTime, onupdate=now)

