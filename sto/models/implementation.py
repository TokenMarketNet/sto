"""Attach SQLAlchemy models to their "Base"

The framework user may supply their own base class e.g. for the case of fine tuning some database options.
Here we supply implementations for the default command line application using SQLite.
"""

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from .broadcastaccount import _BroadcastAccount, _PreparedTransaction
from .tokenscan import _TokenScanStatus, _TokenHolderDelta, _TokenHolderAccount


Base = declarative_base()


class BroadcastAccount(_BroadcastAccount, Base):
    pass


class PreparedTransaction(_PreparedTransaction, Base):

    broadcast_account_id = sa.Column(sa.ForeignKey("broadcast_account.id"), nullable=True)
    broadcast_account = orm.relationship(BroadcastAccount,
                        backref=orm.backref("txs",
                                        lazy="dynamic",
                                        cascade="all, delete-orphan",
                                        single_parent=True, ), )


class TokenScanStatus(_TokenScanStatus, Base):
    pass


class TokenHolderAccount(_TokenHolderAccount, Base):

    token_id = sa.Column(sa.ForeignKey("token_scan_status.id"), nullable=False)
    token = orm.relationship(TokenScanStatus,
                        backref=orm.backref("accounts",
                                        lazy="dynamic",
                                        cascade="all, delete-orphan",
                                        single_parent=True, ), )


class TokenHolderDelta(_TokenHolderDelta, Base):

    account_id = sa.Column(sa.ForeignKey("token_holder_account.id"), nullable=False)
    account = orm.relationship(TokenHolderAccount,
                        backref=orm.backref("deltas",
                                        lazy="dynamic",
                                        cascade="all, delete-orphan",
                                        single_parent=True, ), )


