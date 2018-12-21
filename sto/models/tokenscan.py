"""Helper models to get token balances in the past (point of time, block num)."""
from binascii import hexlify
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm.attributes import flag_modified

from sto.models.utils import TimeStampedBaseModel


class _TokenScanStatus(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.
    """

    __tablename__ = "token_scan_status"

    #: Which network e.g. "ethereum", "kovan"
    network = sa.Column(sa.String(256), nullable=False, unique=False)

    #: Address of the token contract, as hex string 0x00000, Ethereum checksummed
    address = sa.Column(sa.String(256), nullable=False, unique=False)

    #: First block that was scanned (usually when the contract was deployed)
    start_block = sa.Column(sa.Integer, nullable=True)

    #: End block
    end_block = sa.Column(sa.Integer, nullable=True)

    #: When the end block was timestamped
    end_block_timestamp = sa.Column(sa.DateTime, nullable=True)

    #: All token balances are stored in raw amounts
    decimals = sa.Column(sa.Integer, nullable=False)



class _TokenHolderDelta(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.

    This is an SQLite specific hack, as it does not support 256 bit integers or true decimal types.
    """

    __tablename__ = "token_holder_delta"

    #: Token holder address, Ethereum checksummed
    address = sa.Column(sa.String(256), nullable=False, unique=False)

    #: First block that was scanned (usually when the contract was deployed)
    block_num = sa.Column(sa.Integer, nullable=True)

    #: Order of this event within the block, as one block may trigger multiple events
    block_internal_order = sa.Column(sa.Integer, nullaxle=True)

    #: Give us direct link to this transaction
    txid = sa.Column(sa.String(256), nullable=True, unique=False)

    #: Raw uint256 data
    raw_delta = sa.Column(sa.Binary(32), nullable=True, unique=False)

    def get_delta_uint(self):
        """Return the delta as Python unlimited integer."""
        return int(hexlify(self.raw_delta), 16)

    def set_delta_uint(self, val):
        """Return the delta as Python """
        b = val.to_bytes(8, byteorder="big")
        self.raw_delta = b


class _TokenHolderLastBalance(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.
    """

    __tablename__ = "token_scan_status"

    #: Address of the token contract, as hex string 0x00000
    address = sa.Column(sa.String(256), nullable=False, unique=False)

    #: End block
    last_updated_block = sa.Column(sa.Integer, nullable=True)

    #: Raw uint256 data
    raw_balance = sa.Column(sa.Binary(32), nullable=True, unique=False)

    #: When the end block was timestamped
    last_block_updated_at = sa.Column(sa.DateTime, nullable=True)

    def get_balance_uint(self):
        """Return the delta as Python unlimited integer."""
        return int(hexlify(self.raw_balance), 16)

    def set_balance_uint(self, val):
        """Return the delta as Python """
        b = val.to_bytes(8, byteorder="big")
        self.raw_balance = b
