"""Helper models to get token balances in the past (point of time, block num).


Please note that this implementation is reference only, SQLite compatible.
Efficiency can be greatly increased by

- Create a table Blocks which holds the reference to scanned blocks - drop blocks if they are forked

- Using binary storage for addresses, transaction hashes and such

- Using native uint256 column for values

- Calculate holder balances on the database side instead of iterating them on the application side
"""
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

    def get_total_token_holder_count(self, include_empty=False):
        """How many addresses are/have been holding this token."""
        q = self.balances

        if include_empty:
            pass
        else:
            q = q.filter_by(empty=False)

        return q.count()


class _TokenHolderDelta(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.

    Each token transfer creates two delta events
    - Credit event: to account, positive balance change
    - Debit event: from account, negative balance change

    This is an SQLite specific hack, as it does not support 256 bit integers or true decimal types.=
    """

    NULL_ADDRESS = "0x0000000000000000000000000000000000000000"  # Used as an address in new issuances when "from" is not available

    __tablename__ = "token_holder_delta"

    #: Token holder address, Ethereum checksummed
    address = sa.Column(sa.String(256), nullable=False, unique=False)

    #: First block that was scanned (usually when the contract was deployed)
    block_num = sa.Column(sa.Integer, nullable=True)

    #: When the block was timestamped
    block_timestamped_at = sa.Column(sa.DateTime, nullable=True)

    #: Give us direct link to this transaction
    txid = sa.Column(sa.String(256), nullable=True, unique=False)

    #: Order of this event within the transaction, as one transaction may trigger multiple Transfer events within smart contracts
    tx_internal_order = sa.Column(sa.Integer, nullable=True)

    #: Raw uint256 data
    raw_delta = sa.Column(sa.Binary(32), nullable=False, unique=False)

    #: Because raw values are uint256 and we deal with deltas, need to store the sign here. Either +1 or -1
    sign = sa.Column(sa.SmallInteger, nullable=False, unique=False)

    def __str__(self):
        return "<Token:{}, address:{}, block:{}, tx:{} delta:{}>".format(self.token.address, self.address, self.block_num, self.txid, self.get_delta_uint())

    def get_delta_uint(self):
        """Return the delta as Python unlimited integer."""
        return int(hexlify(self.raw_delta), 16) * self.sign

    def set_delta_uint(self, val: int, sign: int):
        """Return the delta as Python """
        assert type(val) == int
        b = val.to_bytes(32, byteorder="big")
        self.raw_delta = b
        self.sign = sign


class _TokenHolderLastBalance(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.
    """

    __tablename__ = "token_holder_last_balance"

    #: Address of the token contract, as hex string 0x00000
    address = sa.Column(sa.String(256), nullable=False, unique=False)

    #: Raw uint256 data
    raw_balance = sa.Column(sa.Binary(32), nullable=True, unique=False)

    #: Because sqlite cannot query uint256, we have this hack to query zero balances
    empty = sa.Column(sa.Boolean, nullable=False)

    #: End block
    last_updated_block = sa.Column(sa.Integer, nullable=True)

    #: When the end block was timestamped
    last_block_updated_at = sa.Column(sa.DateTime, nullable=True)

    def __str__(self):
        return "<Token:{}, holder:{}, updated at:{}, balance:{}>".format(self.token.address, self.address, self.last_updated_block, self.get_balance_uint())

    def get_balance_uint(self):
        """Return the delta as Python unlimited integer."""
        return int(hexlify(self.raw_balance), 16)

    def set_balance_uint(self, val: int):
        """Return the delta as Python """
        assert type(val) == int
        b = val.to_bytes(32, byteorder="big")
        self.raw_balance = b

        if val:
            self.empty = False
        else:
            self.empty = True
