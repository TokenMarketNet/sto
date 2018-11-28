import binascii
from logging import Logger

from eth_account.account import Account


def create_account_console(logger: Logger):
    """Creates an Ethereum account and echoes the details to console."""

    acc = Account.create()
    logger.info("Account address: %s", acc.address)
    logger.info("Account private key: %s", binascii.hexlify(acc.privateKey).decode("ascii"))
