import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

from .broadcastaccount import _BroadcastAccount, _PreparedTransaction


Base = declarative_base()


#
# We have split up models to two separate files without base to ensure they can reused across different Python projects
#

class BroadcastAccount(_BroadcastAccount, Base):
    pass


class PreparedTransaction(_PreparedTransaction, Base):

    broadcast_account_id = sa.Column(sa.ForeignKey("broadcast_account.id"), nullable=True)
    broadcast_account = orm.relationship(BroadcastAccount,
                        backref=orm.backref("txs",
                                        lazy="dynamic",
                                        cascade="all, delete-orphan",
                                        single_parent=True, ), )
