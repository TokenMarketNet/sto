import datetime
from logging import Logger

from decimal import Decimal
from sqlalchemy.orm import Session, Query
from typing import Optional, List

from sto.identityprovider import IdentityProvider
from sto.models.implementation import TokenHolderLastBalance


class NeedsTokenScan(Exception):
    pass


class CapTableEntry:
    """Reveal real world identity behind an address.

    Used when priting out cap table.
    """

    def __init__(self, name: str, address: str, balance: Decimal, updated_at: datetime.datetime):
        """
        :param name: Entity name or person name
        :param address: Crypto address where STOs are delivered
        """
        self.name = name
        self.address = address
        self.balance = balance
        self.percent = None
        self.updated_at = updated_at


def sort_entries(entries: List[CapTableEntry], sort_order: str):
    """Sort constructed cap table in place.

    Match friendly sort order to its underlying SQLite query.
    """
    if sort_order == "balance":
        c = lambda entry: entry.balance
    elif sort_order == "name":
        c = lambda entry: entry.name
    elif sort_order == "updated":
        c = lambda entry: entry.name
    else:
        raise RuntimeError("Unknown sort order")


def cap_table(logger: Logger,
              dbsession: Session,
              token_address: str,
              sort_order: str,
              identity_provider: Optional[IdentityProvider],
              include_empty: bool,
              TokenScanStatus: type,
              TokenHolderLastBalance: type,
              no_name="<Unknown>") -> List[CapTableEntry]:
    """Print out cap table.

    :param sort_order: "balance", "name", "updated", "address"
    :param include_empty: Include accounts that hold balance in the past
    :param TokenScanStatus: Token scan model used
    :param TokenHolderLastBalance: Token balance model used
    :return: List of CapTable entries
    """

    status = dbsession.query(TokenScanStatus).filter_by(token_address=token_address).one_or_none()
    if not status or status.end_block is None:
        raise NeedsTokenScan("No token holder balances available in the local database. Please run sto token-scan first.")

    q = status.get_balances(include_empty)

    results = []
    total_balance = Decimal(0)
    for holder in q:
        name = identity_provider.get_identity(holder.addess)
        if not name:
            name = no_name
        decimal_balance = holder.get_decimal_balance()
        results.append(CapTableEntry(name, holder.address, decimal_balance))

    sort_entries(results, sort_order)

    # Retrofit decimal balances after we know the total sum
    if total_balance > 0:
        for r in results:
            r.percent = r.balance / total_balance

    return results










