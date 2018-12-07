import binascii
from logging import Logger

import colorama
from eth_account.account import Account
from eth_utils import to_hex

CONFIG_FILE_TEMPLATE = """

#
# Your STO configuration file for {network}
#

network = {network}

# Where to connect for Parity or Geth JSON-RPC API
ethereum-node-url = http://localhost:8545

# The private key for your generated Ethereum account {address}
ethereum-private-key = {private_key}
"""


def create_account_console(logger: Logger, network: str):
    """Creates an Ethereum account and echoes the details to console."""

    acc = Account.create()
    private_key = to_hex(acc.privateKey)
    logger.info("Account address: %s", acc.address)
    logger.info("Account private key: %s", private_key)

    config = CONFIG_FILE_TEMPLATE.format(private_key=private_key, network=network, address=acc.address)
    config_file_name = "myconfig.ini"

    print()
    print("Create a file {}{}{} and paste in the following content: {}{}{}".format(colorama.Fore.LIGHTBLUE_EX, config_file_name, colorama.Fore.RESET, colorama.Fore.LIGHTBLACK_EX, config, colorama.Fore.RESET))
    print()
    print("After this you can run {}sto --config-file={} diagnose{}".format(colorama.Fore.LIGHTBLUE_EX, config_file_name, colorama.Fore.RESET))