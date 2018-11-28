import binascii
import calendar
import datetime
import time

from logging import Logger

from typing import Optional

from eth_account import Account
from eth_utils import from_wei
from web3 import Web3, HTTPProvider
from corporategovernance.ethereum.utils import check_good_node_url


class NodeNotSynced(Exception):
    pass


class NeedMoney(Exception):
    pass


def diagnose(logger: Logger, node_url: str, private_key_hex: str) -> Optional[Exception]:
    """Run Ethereum connection and account diagnostics.

    Check that the user has properly configured Ethereum node and private key.

    Never fails. Exceptions are written to the logger output and returned.
    """

    try:
        check_good_node_url(node_url)

        logger.info("Attempting to connect to Ethereum node %s", node_url)
        web3 = Web3(HTTPProvider(node_url))

        logger.info("Connected to Ethereum node software %s", web3.version.node)

        block_num = web3.eth.blockNumber

        d = datetime.datetime.utcnow()
        unix_time = calendar.timegm(d.utctimetuple())

        block_info = web3.eth.getBlock(block_num)
        last_time = block_info["timestamp"]

        if last_time == 0:
            raise NodeNotSynced("Looks like your node has not yet been synced.")

        ago = unix_time - last_time

        logger.info("Current Ethereum node block number: %d, last block %d seconds ago - compare this to data on https://etherscan.io", block_num, ago)

        if ago < 0:
            raise NodeNotSynced("Last block in the future? Do we have a clock with a wrong timezone somewhere?")

        if ago > 1800:
            raise NodeNotSynced("Looks like your node has not received a block for half an hour. It is most likely unsynced at the moment.")

        if not private_key_hex:
            raise NeedPrivateKey("No private key configured. This application signs transactions locally and needs to have a private key configured. See manual for more instructions.")

        logger.info("Using private key %s...", private_key_hex[0:3])
        account = Account.privateKeyToAccount(binascii.unhexlify(private_key_hex))

        balance = web3.eth.getBalance(account.address)
        logger.info("Address %s has ETH balance of %f", account.address, from_wei(balance, "ether"))

        if balance == 0:
            raise NeedMoney("Your Ethereum account {} needs to have ETH in order to use this tool".format(account.address))


    except Exception as e:

        logger.error("Diagnostics failure")
        logger.exception(e)
        return e