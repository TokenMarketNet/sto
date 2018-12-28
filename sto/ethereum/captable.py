from logging import Logger

from decimal import Decimal
from sqlalchemy.orm import Session
from typing import Optional, List

from sto.identityprovider import IdentityProvider


class NeedsTokenScan(Exception):
    pass


class CapTableEntry:
    """Reveal real world identity behind an address.

    Used when priting out cap table.
    """

    def __init__(self, name: str, address: str, amount: Decimal, percent: Decimal):
        """
        :param name: Entity name or person name
        :param address: Crypto address where STOs are delivered
        """
        self.name = name
        self.address = address
        self.amount = amount
        self.percent = percent


def cap_table(logger: Logger,
              dbsession: Session,
              token_address: str,
              sort_order: str,
              identity_provider: Optional[IdentityProvider],
              TokenScanStatus: type,
              TokenHolderLastBalance: type) -> List[CapTableEntry]:
    """Print out cap table.

    :param sort_order: "amount", "name", "table"
    :param TokenScanStatus: Token scan model used
    :param TokenHolderLastBalance: Token balance model used
    :return: List of CapTable entries
    """

    status = dbsession.query(TokenScanStatus).filter_by(token_address=token_address).one_or_none()
    if not status or status.end_block is None:
        raise NeedsTokenScan("No token holder balances available in the local database. Please run sto token-scan first.")

    q = status.balances
    if sort_order == "amount":
        q = q.order_by(TokenHolderLastBalance)

    for holder in status.balances:
        pass




