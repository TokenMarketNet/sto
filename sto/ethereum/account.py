import binascii
from logging import Logger

from eth_account.account import Account
from eth_utils import to_hex

CONFIG_FILE_TEMPLATE = """

#
# Your STO configuration file for {network}
#

network = kovan

# Where to connect for Parity or Geth JSON-RPC API
ethereum-node-url = http://localhost:8545

# The private key for your generated Ethereum account
ethereum-private-key = {private_key}
"""


def create_account_console(logger: Logger, network: str):
    """Creates an Ethereum account and echoes the details to console."""

    acc = Account.create()
    private_key = to_hex(acc.privateKey)
    logger.info("Account address: %s", acc.address)
    logger.info("Account private key: %s", private_key)

    config = CONFIG_FILE_TEMPLATE.format(private_key=private_key, network=network)
    config_file_name = "myconfig.ini"

    print("Create a file {} and paste in the following content:".format(config_file_name))
    print()
    print(config)