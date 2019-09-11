from logging import Logger

from sto.friendlytime import pretty_date

from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import check_good_private_key, create_web3, mk_contract_address, get_abi, \
    get_contract_deployed_tx
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
    ethereum_abi_file: str=None,
    commit=True,
):
    check_good_private_key(ethereum_private_key)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    service.ensure_accounts_in_sync()

    account = service.get_or_create_broadcast_account()
    abi = get_abi(ethereum_abi_file)
    # read nonce from the network
    tx_count = web3.eth.getTransactionCount(service.address)
    pending_txs = service.get_account_pending_broadcasts()
    _nonce = tx_count
    old_new_contract_address = {}
    for tx in pending_txs:
        tx.nonce = _nonce
        tx.unsigned_payload['nonce'] = _nonce
        if tx.contract_address:
            if tx.contract_deployment:
                old_address = tx.contract_address
                tx.contract_address = mk_contract_address(service.address, _nonce)
                old_new_contract_address[old_address] = tx.contract_address
        if tx.other_data.get('extra_data', {}).get('contract_address', None):
                old_address = tx.other_data['extra_data']['contract_address']
                assert old_address in old_new_contract_address, "old address mapping not found"
                new_address = old_new_contract_address[old_address]
                tx.contract_address = new_address
                contract = service.get_contract_proxy(
                    tx.other_data['extra_data']['contract_name'],
                    abi,
                    new_address,
                    use_bytecode=True
                )
                func = contract.get_function_by_name(tx.other_data['extra_data']['func_name'])
                tx_data = service.generate_tx_data(_nonce)
                args = tx.other_data['extra_data']['args']

                # HACK JUST TO SHOW WHAT IS HAPPENING
                if 'newVerifier' in args:
                    # bigger problem: There's no way to know
                    # whether UnrestrictedTransferAgent or RestrictedTransferAgent was used
                    args['newVerifier'] = get_contract_deployed_tx(dbsession, 'UnrestrictedTransferAgent').contract_address

                constructed_txn = func(**args).buildTransaction(tx_data)
                tx.unsigned_payload = constructed_txn

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
