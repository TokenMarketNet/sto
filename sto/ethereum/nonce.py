from logging import Logger

from sto.friendlytime import pretty_date

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key, create_web3
from sto.models.implementation import BroadcastAccount, PreparedTransaction

from sqlalchemy.orm import Session


class HistoryDeleteNeeded(Exception):
    pass


def restart_nonce(
    logger: Logger,
    dbsession: Session,
    network: str,
    ethereum_node_url: str,
    ethereum_private_key: str,
    ethereum_gas_limit: str,
    ethereum_gas_price: str,
    commit=True
):
    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    service.ensure_accounts_in_sync()

    account = service.get_or_create_broadcast_account()
    # read nonce from the network
    tx_count = web3.eth.getTransactionCount(service.address)
    pending_txs = service.get_account_pending_broadcasts()
    _nonce = tx_count
    for tx in pending_txs:
        tx.nonce = _nonce
        tx.unsigned_payload['nonce'] = _nonce
        _nonce += 1

    # record to the database
    account.current_nonce = _nonce

    logger.info("Address %s, nonce is now set to %d", service.address, account.current_nonce)
    if commit:
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
