import datetime
import time

from logging import Logger

from typing import Optional

from web3 import Web3
from corporategovernance.ethereum.utils import check_good_node_url



def diagnose(logger: Logger, node_url: str) -> Optional[Exception]:
    """Run Ethereum connection and account diagnostics.

    Never fails. Exceptions are written to the logger output and returned.
    """

    try:
        check_good_node_url(node_url)

        logger.info("Attempting to connect to Ethereum node %s", node_url)
        web3 = Web3(node_url)

        block_num = web3.eth.blockNumber

        now = datetime.datetime.utcnow()
        unix_time = time.mktime(now.timetuple())

        block_info = web3.eth.getBlockInfo(block_num)
        ago = unix_time - block_info[time]

        logger.info("Current Ethereum block number: %d, %d seconds ago", block_num, ago)
    except Exception as e:
        logger.error("Diagnostics failure %s", e)
        logger.exception(e)
        return e