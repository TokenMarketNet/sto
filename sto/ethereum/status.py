from logging import Logger
from tqdm import tqdm

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key, create_web3
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from eth_account import Account
from eth_utils import to_bytes, from_wei
from sqlalchemy.orm import Session
from typing import Union
from web3 import Web3, HTTPProvider


def update_status(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: Union[str, Web3],
              ethereum_private_key: str,
              ethereum_gas_limit: str,
              ethereum_gas_price: str,
):
    """Issue out a new Ethereum token."""

    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    unfinished_txs = service.get_unmined_txs()

    logger.info("Updating status for %d unfinished transactions for broadcasting in network %s", unfinished_txs.count(), network)

    if unfinished_txs.count() == 0:
        logger.info("No transactions to update. Use sto tx-last command to show the status of the last transactions.")
        return []

    unfinished_txs = list(unfinished_txs)

    # https://stackoverflow.com/questions/41985993/tqdm-show-progress-for-a-generator-i-know-the-length-of
    for tx in tqdm(unfinished_txs):
        service.update_status(tx)
        dbsession.commit()  # Try to minimise file system sync issues

    return unfinished_txs
