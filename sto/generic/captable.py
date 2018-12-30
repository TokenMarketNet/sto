import datetime
from logging import Logger

from decimal import Decimal

import colorama
from sqlalchemy.orm import Session, Query
from typing import Optional, List

from sto.identityprovider import IdentityProvider
from sto.models.tokenscan import _TokenScanStatus
from sto.time import friendly_time


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


class CapTableInfo:
    """Information about the cap table.

    For command line and web UIs to use.
    """

    def __init__(self, token_status: _TokenScanStatus, last_token_transfer_at, total_balance, entries):
        self.token_status = token_status
        self.last_token_transfer_at = last_token_transfer_at
        self.entries = entries
        self.total_balance = total_balance


def sort_entries(entries: List[CapTableEntry], order_by: str, order_direction: str):
    """Sort constructed cap table in place.

    Match friendly sort order to its underlying SQLite query.
    """
    if order_by == "balance":
        key = lambda entry: entry.balance
    elif order_by == "name":
        key = lambda entry: entry.name
    elif order_by == "updated":
        key = lambda entry: entry.updated_at
    elif order_by == "address":
        key = lambda entry: entry.address
    else:
        raise TypeError("Unknown sort order")

    if order_direction == "asc":
        entries.sort(key=key)
    elif order_direction == "desc":
        entries.sort(key=key, reverse=True)
    else:
        raise TypeError("Unknown sort direction")


def generate_cap_table(logger: Logger,
              dbsession: Session,
              token_address: str,
              order_by: str,
              order_direction: str,
              identity_provider: IdentityProvider,
              include_empty: bool,
              TokenScanStatus: type,
              TokenHolderAccount: type,
              no_name="<Unknown>") -> CapTableInfo:
    """Print out cap table.

    :param sort_order: "balance", "name", "updated", "address"
    :param include_empty: Include accounts that hold balance in the past
    :param TokenScanStatus: Token scan model used
    :param TokenHolderAccount: Token balance model used
    :return: List of CapTable entries
    """

    status = dbsession.query(TokenScanStatus).filter_by(address=token_address).one_or_none()  # type: TokenScanStatus
    if not status or status.end_block is None:
        raise NeedsTokenScan("No token {} balances available in the local database. Please run sto token-scan first.".format(token_address))

    q = status.get_accounts(include_empty)

    results = []
    total_balance = Decimal(0)
    last_token_transfer_at = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    for holder in q:

        id_check = identity_provider.get_identity(holder.address)
        if id_check:
            name = id_check.name
        else:
            name = no_name

        decimal_balance = holder.get_decimal_balance()

        entry = CapTableEntry(name, holder.address, decimal_balance, holder.last_block_updated_at)

        if entry.updated_at > last_token_transfer_at:
            last_token_transfer_at = entry.updated_at
        results.append(entry)

        if  decimal_balance > 0:  # Ignore cases where we cannot detect mint transaction
            total_balance += decimal_balance

    sort_entries(results, order_by, order_direction)

    # Retrofit decimal balances after we know the total sum
    if total_balance > 0:
        for r in results:
            r.percent = r.balance / total_balance

    info = CapTableInfo(status, last_token_transfer_at, total_balance, results)

    return info


def print_cap_table(info: CapTableInfo, max_entries: int, accuracy: int):
    """Console cap table printer"""

    if not info.token_status.end_block_timestamp:
        print("{}Token address {} not scanned. Please run sto token-scan first.{}".format(colorama.Fore.RED, info.token_status.address, colorama.Fore.RESET))
        return

    print("Token address: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, info.token_status.address, colorama.Fore.RESET))
    print("Name: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, info.token_status.name, colorama.Fore.RESET))
    print("Symbol: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, info.token_status.symbol, colorama.Fore.RESET))
    print("Total supply: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, info.token_status.total_supply, colorama.Fore.RESET))
    print("Accounted supply: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, info.total_balance, colorama.Fore.RESET))
    print("Holder count: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, len(info.entries), colorama.Fore.RESET))
    print("Cap table database updated at: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, friendly_time(info.token_status.end_block_timestamp), colorama.Fore.RESET))
    print("Last token transfer at at: {}{}{}".format(colorama.Fore.LIGHTCYAN_EX, friendly_time(info.last_token_transfer_at), colorama.Fore.RESET))

    print_entries = info.entries[0:max_entries]

    table = []

    balance_q = Decimal(10) ** Decimal(-accuracy)
    percent_q = Decimal("0.01")

    # Tuplify
    for idx, entry in enumerate(print_entries, start=1):
        table.append((
            idx,
            entry.name,
            entry.address,
            entry.updated_at,
            "{:,}".format(entry.balance.quantize(balance_q)),
            str(((entry.percent or 0) * Decimal(100)).quantize(percent_q)),
        ))

    from tabulate import tabulate  # https://bitbucket.org/astanin/python-tabulate
    output = tabulate(table, headers=["#", "Name", "Address", "Last transfer", "Balance", "%"], disable_numparse=True)
    print(output)






