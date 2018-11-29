from logging import Logger
from tqdm import tqdm

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key, create_web3
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from eth_account import Account
from eth_utils import to_bytes, from_wei
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider


def get_last_transactions(logger: Logger,
              dbsession: Session,
              network: str,
              limit: int,
              ethereum_node_url: str,
              ethereum_private_key: str,
              ethereum_gas_limit: str,
              ethereum_gas_price: str,
):
    """Issue out a new Ethereum token."""

    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    last_txs = service.get_last_transactions(limit)
    if last_txs.count() == 0:
        logger.info("No transactions yet")
        return []

    return list(last_txs)
