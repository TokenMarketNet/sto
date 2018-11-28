"""Issuing out tokenised shares."""
from logging import Logger

from sto.ethereum.manifest import get_package
from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import get_abi, check_good_private_key
from sto.models.implementation import BroadcastAccount, PreparedTransaction
from sqlalchemy.orm import Session
from web3 import Web3, HTTPProvider
from web3.contract import Contract


def deploy_token_contracts(logger: Logger,
                          dbsession: Session,
                          network: str,
                          ethereum_node_url: str,
                          ethereum_abi_file: str,
                          ethereum_private_key: str,
                          ethereum_gas_limit: str,
                          ethereum_gas_price: str,
                          name: str,
                          symbol: str,
                          amount: int,
                          transfer_restriction: str):
    """Issue out a new Ethereum token."""

    check_good_private_key(ethereum_private_key)

    abi = get_abi(ethereum_abi_file)

    web3 = Web3(HTTPProvider(ethereum_node_url))

    # We do not have anything else implemented yet
    assert transfer_restriction == "unrestricted"

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    # Deploy security token
    note = "Token contract for {}".format(name)
    deploy_tx1 = service.deploy_contract("SecurityToken", abi, note, constructor_args={"_name": name, "_symbol": symbol})  # See SecurityToken.sol

    # Deploy transfer agent
    note = "Unrestricted transfer manager for {}".format(name)
    deploy_tx2 = service.deploy_contract("UnrestrictedTransferAgent", abi, note)

    # Set transfer agent
    note = "Setting security token transfer manager for {}".format(name)
    contract_address = deploy_tx1.contract_address
    update_tx1 = service.interact_with_contract("SecurityToken", abi, contract_address, note, "setTransactionVerifier", {"newVerifier": deploy_tx1.contract_address})

    # Issue out initial shares
    note = "Creating {} initial shares for {}".format(amount, name)
    contract_address = deploy_tx1.contract_address
    amount_18 = int(amount) * 10**18
    update_tx2 = service.interact_with_contract("SecurityToken", abi, contract_address, note, "issueTokens", {"value": amount_18})

    logger.info("Prepared transactions for broadcasting for network %s", network)
    return [deploy_tx1, deploy_tx2, update_tx1, update_tx2]









