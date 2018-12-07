"""Share distribution functionalities."""
import csv
from decimal import Decimal
from logging import Logger

from typing import List

from sto.ethereum.utils import validate_ethereum_address


class DistributionEntry:
    """Hold information about who is going to receive the share.

    Used to harmonise different input and output formats.
    """

    def __init__(self, external_id: str, email: str, name: str, address: str, amount: Decimal):
        """
        :param external_id: External transaction id - always unique - like a TXID for Ethereum or a fiat payment reference number.
        :param email: We pass email ids around as they are generally easy way to identity entities across systems in human readable manner - think Asian letters
        :param name: Entity name or person name
        :param address: Crypto address where STOs are delivered
        :param amount: Amount of STO
        """
        self.external_id = external_id
        self.email = email
        self.name = name
        self.address = address
        self.amount = amount

    def __json__(self):
        """Convert for JSON export."""
        return {
            "external_id": self.external_id,
            "name": self.name,
            "address": self.address,
            "email": self.email,
            "amount": str(self.amount)
        }


def read_csv(logger: Logger, fname) -> List[DistributionEntry]:
    """Read outgoing distribution records from CSV file.

    Columns are:
    * external_id
    * email
    * name
    * address
    * amount
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
            raise ValueError("Invalid Ethereum address on row:" + str(idx+1) + " address:", addr +  " reason:" + str(e) + " external_id:" + row["external_id"]) from e

        amount = row["amount"].strip()
        try:
            amount = Decimal(amount)
        except ValueError as e:
            raise ValueError("Invalid decimal amounton row:" + str(idx+1) + " amount:", addr +  " reason:" + str(e) + " external_id:" + row["external_id"]) from e

        entry = DistributionEntry(row["external_id"], row["email"], row["name"], row["address"], amount)
        result.append(entry)

    return result



