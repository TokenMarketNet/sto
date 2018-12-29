"""Helper models to get token balances in the past (point of time, block num).


Please note that this implementation is reference only, SQLite compatible.
Efficiency can be greatly increased by

- Create a table Blocks which holds the reference to scanned blocks - drop blocks if they are forked

- Using binary storage for addresses, transaction hashes and such

- Using native uint256 column for values

- Calculate holder balances on the database side instead of iterating them on the application side
"""
import datetime
from binascii import hexlify
from typing import Optional, Tuple, Dict, Iterable

import sqlalchemy as sa
from decimal import Decimal

from sqlalchemy.orm import Query, object_session
from sqlalchemy.orm.attributes import flag_modified

from sto.models.utils import TimeStampedBaseModel, UTCDateTime, now


class _TokenScanStatus(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.

    """

    NULL_ADDRESS = "0x0000000000000000000000000000000000000000"  # Used as an address in new issuances when "from" is not available

    __tablename__ = "token_scan_status"

    #: Which network e.g. "ethereum", "kovan"
    network = sa.Column(sa.String(256), nullable=False)

    #: Address of the token contract, as hex string 0x00000, Ethereum checksummed
    address = sa.Column(sa.String(256), nullable=False)

    #: First block that was scanned (usually when the contract was deployed)
    start_block = sa.Column(sa.Integer, nullable=True)

    #: End block
    end_block = sa.Column(sa.Integer, nullable=True)

    #: When the end block was timestamped
    end_block_timestamp = sa.Column(UTCDateTime, nullable=True)

    #: Token name
    name = sa.Column(sa.String(256), nullable=True)

    #: Ticker symbol
    symbol = sa.Column(sa.String(256), nullable=True)

    #: All token balances are stored in raw amounts
    decimals = sa.Column(sa.Integer, nullable=False, default=0)

    #: Total supply, as stringified decimal
    total_supply = sa.Column(sa.String(256), nullable=True)

    def get_accounts(self, include_empty=False) -> Query:
        q = self.accounts
        if include_empty:
            pass
        else:
            q = q.filter_by(empty=False)
        return q

    def get_total_token_holder_count(self, include_empty=False):
        """How many addresses are/have been holding this token."""
        return self.get_accounts(include_empty).count()

    def get_or_create_account(self, token_holder: str) -> "_TokenHolderAccount":
        """Denormalize the token balance.

        Drop in a PostgreSQL implementation here using native databae types.
        """
        assert token_holder.startswith("0x")

        TokenHolderAccount = self.accounts.attr.target_mapper.class_

        account = self.accounts.filter_by(address=token_holder).one_or_none()
        if not account:
            account = TokenHolderAccount(address=token_holder)
            self.accounts.append(account)
        return account

    def create_deltas(self, block_num: int, block_when: datetime, txid: str, idx: int, from_: str, to_: str, value: int, TokenHolderDelta: type):
        """Creates token balance change events in the database.

        For each token transfer we create debit and credit events, so that we can nicely sum the total balance of the account.

        :param block_num: Block number
        :param block_when: Block timestamp
        :param txid: Transaction hash
        :param idx: Log index within the transaction
        :param from_: Debit account
        :param to_: Credit account
        :param value: uint256 transfer value
        """
        assert txid.startswith("0x")
        assert from_.startswith("0x")
        assert to_.startswith("0x")

        TokenHolderAccount = self.accounts.attr.target_mapper.class_

        existing = TokenHolderDelta.get_all_deltas(self).filter_by(block_num=block_num, tx_internal_order=idx).first()
        if existing:
            raise RuntimeError("Had already existing imported event: {}".format(existing))

        credit_account = self.get_or_create_account(to_)
        delta_credit = TokenHolderDelta(block_num=block_num, txid=txid, tx_internal_order=idx, block_timestamped_at=block_when)
        delta_credit.set_delta_uint(value, +1)
        credit_account.add_delta(delta_credit)

        if from_ != self.NULL_ADDRESS:
            debit_account = self.get_or_create_account(from_)
            delta_debit = TokenHolderDelta(block_num=block_num, txid=txid, tx_internal_order=idx, block_timestamped_at=block_when)
            delta_debit.set_delta_uint(value, -1)
            debit_account.add_delta(delta_debit)

    def get_raw_balance(self, address) -> int:
        """Get uint256 token balance of an address."""
        account = self.get_or_create_account(address)
        return account.get_balance_uint()

    def get_raw_balances(self, addresses: Iterable[str]) -> Dict[str, int]:
        """Get address -> balance mappings"""
        return {a: self.get_raw_balance(a) for a in addresses}

    def update_denormalised_balances(self):
        """Calculate new balance on all accounts that have been marked dirty since the last scan."""
        for account in self.accounts.filter_by(balance_calculated_at=None):
            account.update_denormalised_balance()


class _TokenHolderDelta(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.

    Each token transfer creates two delta events
    - Credit event: to account, positive balance change
    - Debit event: from account, negative balance change

    This is an SQLite specific hack, as it does not support 256 bit integers or true decimal types.=
    """

    __tablename__ = "token_holder_delta"

    #: First block that was scanned (usually when the contract was deployed)
    block_num = sa.Column(sa.Integer, nullable=True)

    #: When the block was timestamped
    block_timestamped_at = sa.Column(UTCDateTime, nullable=True)

    #: Give us direct link to this transaction
    txid = sa.Column(sa.String(256), nullable=True)

    #: Order of this event within the transaction, as one transaction may trigger multiple Transfer events within smart contracts
    tx_internal_order = sa.Column(sa.Integer, nullable=True)

    #: Raw uint256 data
    raw_delta = sa.Column(sa.Binary(32), nullable=False)

    #: Because raw values are uint256 and we deal with deltas, need to store the sign here. Either +1 or -1
    sign = sa.Column(sa.SmallInteger, nullable=False)

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

    @classmethod
    def get_all_deltas(cls, status: _TokenScanStatus) -> Query:
        """Get all deltas related to this token."""
        return status.accounts.join(cls)

    @classmethod
    def delete_potentially_forked_block_data(cls, status: _TokenScanStatus, after_block: int):
        """Get all deltas related to this token."""

        # TODO: Not sure how this can be offloaded 100% SQL
        session = object_session(status)
        for acc in status.accounts:
            acc.deltas.filter(cls.block_num >= after_block).delete()
            acc.mark_dirty()


class _TokenHolderAccount(TimeStampedBaseModel):
    """Hold the information of which blocks we have scanned for a certain token.

    .. note ::

        We use terms account and address interchangeable in the context of Ethereum.

    """

    __tablename__ = "token_holder_account"

    #: Address of the token contract, as hex string 0x00000
    address = sa.Column(sa.String(256), nullable=False)

    #: Denormalised balance on this account - Raw uint256 data
    #: Calculated from account deltas.
    raw_balance = sa.Column(sa.Binary(32), nullable=True)

    #: Because raw values are uint256 and we deal with deltas, need to store the sign here. Either +1 or -1.
    #: Some ERC-20 balances might go negative if we cannot correctly detect non-standard mint events.
    sign = sa.Column(sa.SmallInteger, nullable=True)

    #: SQLite hack to be able to sort balances
    sortable_balance = sa.Column(sa.Integer, nullable=True)

    #: Because sqlite cannot query uint256, we have this hack to query zero balances
    empty = sa.Column(sa.Boolean, nullable=False, default=True)

    #: When this account saw transfers last time
    last_block_num = sa.Column(sa.Integer, nullable=True)

    #: When the last transfer was timestamped
    last_block_updated_at = sa.Column(UTCDateTime, nullable=True)

    #: When the denormalised balance was calculated last time
    #: Set to null when new deltas arrive
    balance_calculated_at = sa.Column(UTCDateTime, nullable=True, default=None)

    def __str__(self):
        return "<Token:{}, holder:{}, updated at:{}, balance:{}>".format(self.token.address, self.address, self.last_updated_block, self.get_balance_uint())

    def mark_dirty(self):
        """The raw_balance does not """
        self.balance_calculated_at = None

    def is_dirty(self):
        return self.balance_calculated_at is None

    def add_delta(self, delta: _TokenHolderDelta):
        self.deltas.append(delta)
        self.mark_dirty()

    def get_balance_uint(self):
        """Return the delta as Python unlimited integer."""

        if self.is_dirty():
            raise TypeError("You need to calculate denormalised balance first")

        return int(hexlify(self.raw_balance), 16) * self.sign

    def set_balance_uint(self, val: int):
        """Return the delta as Python """

        assert type(val) == int
        b = abs(val).to_bytes(32, byteorder="big")

        self.raw_balance = b
        self.sign = -1 if val < 0 else 1

        if val != 0:
            self.empty = False
        else:
            self.empty = True

        # A hack because SQLite does not support decimals or uint256
        # TODO: Assuming 18 decimals always
        self.sortable_balance = int(Decimal(val) / Decimal(10 ** 18))

    def get_decimal_balance(self) -> Decimal:
        """Get balance in human readable decimal fractions."""
        raw_balance = self.get_balance_uint()
        return Decimal(raw_balance) / (Decimal(10) ** Decimal(self.token.decimals))

    def calculate_sum_from_deltas(self) -> Tuple[int, int, datetime.datetime]:
        """Denormalize the token balance.

        Drop in a more efficient PostgreSQL implementation here using native database types.
        """
        sum = last_block_num = 0
        last_updated_at = None

        TokenHolderDelta = self.deltas.attr.target_mapper.class_

        deltas = self.deltas.order_by(TokenHolderDelta.block_num, TokenHolderDelta.tx_internal_order)
        for d in deltas:
            sum += d.get_delta_uint()
            last_block_num = d.block_num
            last_updated_at = d.block_timestamped_at
        return sum, last_block_num, last_updated_at

    def update_denormalised_balance(self):
        """Denormalise the balance for this account."""
        raw_balance, last_block_num, last_block_at = self.calculate_sum_from_deltas()
        self.set_balance_uint(raw_balance)
        self.last_block_updated_at = last_block_at
        self.last_block_num = last_block_num
        self.balance_calculated_at = now()





