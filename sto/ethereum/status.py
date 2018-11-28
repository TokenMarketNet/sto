from logging import Logger
from tqdm import tqdm

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from eth_account import Account
from eth_utils import to_bytes, from_wei
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider


def update_status(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: str,
              ethereum_private_key: str,
              ethereum_gas_limit: str,
              ethereum_gas_price: str,
):
    """Issue out a new Ethereum token."""

    check_good_private_key(ethereum_private_key)

    web3 = Web3(HTTPProvider(ethereum_node_url))

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    unfinished_txs = service.get_unmined_txs()

    logger.info("Updating status for %d unfinished transactions for broadcasting in network %s", unfinished_txs.count(), network)

    for idx, tx_status in tqdm(enumerate(service.update_status(unfinished_txs))):
        pass

    return list(unfinished_txs)
