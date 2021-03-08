from arrow import Arrow
import datetime


def friendly_time(d: datetime.datetime) -> str:
    """Return "minutes ago" style date"""
    ad = Arrow.fromdatetime(d)
    other = Arrow.fromdatetime(datetime.datetime.utcnow())
    return ad.humanize(other)
