from logging import Logger
from tqdm import tqdm

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key, create_web3
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from eth_account import Account
from eth_utils import to_bytes, from_wei
from sqlalchemy.orm import Session
from typing import Union, Optional
from web3 import Web3, HTTPProvider


def broadcast(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: Union[str, Web3],
              ethereum_private_key: str,
              ethereum_gas_limit: Optional[str],
              ethereum_gas_price: Optional[str],
):
    """Issue out a new Ethereum token."""

    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    service.ensure_accounts_in_sync()

    pending_broadcasts = service.get_pending_broadcasts()

    logger.info("Pending %d transactions for broadcasting in network %s", pending_broadcasts.count(), network)

    if pending_broadcasts.count() == 0:
        logger.info("No new transactions to broadcast. Use sto tx-update command to see tx status.")
        return []

    account = Account.privateKeyToAccount(ethereum_private_key)
    balance = web3.eth.getBalance(account.address)

    logger.info("Our address %s has ETH balance of %f for operations", account.address, from_wei(balance, "ether"))

    txs = list(pending_broadcasts)
    # https://stackoverflow.com/questions/41985993/tqdm-show-progress-for-a-generator-i-know-the-length-of
    for tx in tqdm(txs, total=pending_broadcasts.count()):
        try:
            service.broadcast(tx)
            # logger.info("Broadcasted %s", tx.txid)
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to broadcast transaction %s: %s", tx.txid, tx.human_readable_description)
            raise e

        dbsession.commit()  # Try to minimise file system sync issues

    return txs
