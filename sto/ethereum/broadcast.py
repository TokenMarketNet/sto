from logging import Logger
from tqdm import tqdm

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from eth_account import Account
from eth_utils import to_bytes, from_wei
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider


def broadcast(logger: Logger,
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

    pending_broadcasts = service.get_pending_broadcasts()

    logger.info("Pending %d transactions for broadcasting in network %s", pending_broadcasts.count(), network)

    account = Account.privateKeyToAccount(ethereum_private_key)
    balance = web3.eth.getBalance(account.address)

    logger.info("Our address %s has ETH balance of %f for operations", account.address, from_wei(balance, "ether"))

    for idx, tx_status in tqdm(enumerate(service.broadcast(pending_broadcasts))):
        pass

    return list(pending_broadcasts)
