"""Match Ethereum addresses to real world identities."""
import csv
from abc import ABC
from decimal import Decimal
from logging import Logger

from typing import List, Optional

from eth_utils import to_checksum_address, is_checksum_address

from sto.ethereum.utils import validate_ethereum_address


class IdentityEntry:
    """Reveal real world identity behind an address.

    Used when priting out cap table.
    """

    def __init__(self, name: str, address: str):
        """
        :param name: Entity name or person name
        :param address: Crypto address where STOs are delivered
        """
        self.name = name
        self.address = address


def read_csv(logger: Logger, fname) -> List[IdentityEntry]:
    """Read identity information from a CSV file.

    Columns are:
    * name
    * address
    """

    logger.info("Reading CSV input %s", fname)
    with open(fname, "rt") as inp:
        reader = csv.DictReader(inp)
        rows = [row for row in reader]

    result = []

    # TODO: Address format is now hardcoded for Etheereum.
    for idx, row in enumerate(rows):
        addr = row["address"].strip()
        try:
            validate_ethereum_address(addr)
        except ValueError as e:
            raise ValueError("Invalid Ethereum address on row:" + str(idx+1) + " address:", addr +  " reason:" + str(e) + " name:" + row["name"]) from e

        addr = to_checksum_address(addr)
        entry = IdentityEntry(row["name"], addr)
        result.append(entry)

    return result


class IdentityProvider(ABC):
    """Allow flexible identity backend.

    We can support files, KYC databases, third party services.
    """

    def get_identity(self, address: str) -> Optional[IdentityEntry]:
        """Map address to an identity."""


class NullIdentityProvider(IdentityProvider):
    """Nobody knows who holds the shares. The cryptoanarchist dream.."""

    def __init__(self):
        pass

    def get_identity(self, address) -> Optional[IdentityEntry]:
        return None


class CSVIdentityProvider(IdentityProvider):
    """Hold identities in memory after reading from CSV."""

    def __init__(self, entries: List[IdentityEntry]):
        self.map = {}
        for entry in entries:
            self.map[entry.address] = entry

    def get_identity(self, address) -> Optional[IdentityEntry]:
        assert is_checksum_address(address)
        return self.map.get(address)



