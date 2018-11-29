from logging import Logger

from sto.friendlytime import pretty_date
from tqdm import tqdm

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key, create_web3
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from eth_account import Account
from eth_utils import to_bytes, from_wei
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider



class HistoryDeleteNeeded(Exception):
    pass



def restart_nonce(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: str,
              ethereum_private_key: str,
              ethereum_gas_limit: str,
              ethereum_gas_price: str,
):
    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    service.ensure_accounts_in_sync()

    account = service.get_or_create_broadcast_account()
    txs = service.get_last_transactions(limit=1)
    if txs.count() > 0:
        raise HistoryDeleteNeeded("Cannot reset nonce as the database contains txs for {}. Delete database to restart.".format(service.address))

    # read nonce from the network and record to the database
    tx_count = web3.eth.getTransactionCount(service.address)
    account.current_nonce = tx_count

    logger.info("Address %s, nonce is now set to %d", service.address, account.current_nonce)
    dbsession.commit()


def next_nonce(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: str,
              ethereum_private_key: str,
              ethereum_gas_limit: str,
              ethereum_gas_price: str,
):
    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)
    account = service.get_or_create_broadcast_account()
    ft = pretty_date(account.created_at)
    logger.info("Address %s, created at %s, nonce is now set to %d", service.address, ft, account.current_nonce)