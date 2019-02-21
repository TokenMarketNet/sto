import sqlalchemy as sa

from sto.models.utils import TimeStampedBaseModel, UTCDateTime, now


class _Investor(TimeStampedBaseModel):
    __tablename__ = "investor"

    #: email of investor
    email = sa.Column(sa.String(256), nullable=True)
    # : name of investor
    name = sa.Column(sa.String(500), nullable=True)
    #: Address of the token contract, as hex string 0x00000, Ethereum checksummed
    address = sa.Column(sa.String(256), nullable=False, unique=True)
