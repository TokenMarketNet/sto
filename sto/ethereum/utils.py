import json
import os

from typing import Optional

import colorama
import rlp
from eth_abi import encode_abi
from web3 import Web3, HTTPProvider
from web3.contract import Contract
from web3.utils.abi import get_constructor_abi, merge_args_and_kwargs
from web3.utils.events import get_event_data
from web3.utils.filters import construct_event_filter_params
from eth_utils import (
    keccak,
    to_checksum_address,
    to_bytes,
    is_hex_address,
    is_checksum_address,
    to_hex
)
from web3.utils.contracts import encode_abi
from sqlalchemy import and_

from sto.cli.main import is_ethereum_network


class NoNodeConfigured(Exception):
    pass


class NeedPrivateKey(Exception):
    pass


def check_good_node_url(node_url: str):
    if not node_url:
        raise NoNodeConfigured("You need to give --ethereum-node-url command line option or set it up in a config file")


def check_good_private_key(private_key_hex: str):
    if not private_key_hex:
        raise NeedPrivateKey("You need to give --ethereum-private-key command line option or set it up in a config file")


def get_abi(abi_file: Optional[str]):

    if not abi_file:
        # Use built-in solc output drop
        abi_file = os.path.join(os.path.dirname(__file__), "contracts-flattened.json")

    with open(abi_file, "rt") as inp:
        return json.load(inp)


def create_web3(url: str) -> Web3:
    """Web3 initializer."""

    if isinstance(url, Web3):
        # Shortcut for testing
        return url
    else:
        return Web3(HTTPProvider(url))


def integer_hash(number: int):
    return int(keccak(number).hex(), 16)


def mk_contract_address(sender: str, nonce: int) -> str:
    """Create a contract address using eth-utils.

    https://ethereum.stackexchange.com/a/761/620
    """
    sender_bytes = to_bytes(hexstr=sender)
    raw = rlp.encode([sender_bytes, nonce])
    h = keccak(raw)
    address_bytes = h[12:]
    return to_checksum_address(address_bytes)


# Sanity check
assert mk_contract_address(to_checksum_address("0x6ac7ea33f8831ea9dcc53393aaa88b25a785dbf0"), 1) == to_checksum_address("0x343c43a37d37dff08ae8c4a11544c718abb4fcf8")


def validate_ethereum_address(address: str):
    """Clever Ethereum address validator.

    Assume all lowercase addresses are not checksummed.
    """

    if len(address) < 42:
        raise ValueError("Not an Ethereum address: {}".format(address))

    try:
        if not is_hex_address(address):
            raise ValueError("Not an Ethereum address: {}".format(address))
    except UnicodeEncodeError:
        raise ValueError("Could not decode: {}".format(address))

    # Check if checksummed address if any of the letters is upper case
    if any([c.isupper() for c in address]):
        if not is_checksum_address(address):
            raise ValueError("Not a checksummed Ethereum address: {}".format(address))


def get_constructor_arguments(contract: Contract, args: Optional[list]=None, kwargs: Optional[dict]=None):
    """Get constructor arguments for Etherscan verify.

    https://etherscanio.freshdesk.com/support/solutions/articles/16000053599-contract-verification-constructor-arguments
    """

    # return contract._encode_constructor_data(args=args, kwargs=kwargs)
    constructor_abi = get_constructor_abi(contract.abi)

    # constructor_abi can be none in case of libraries
    if constructor_abi is None:
        return to_hex(contract.bytecode)

    if args is not None:
        return contract._encode_abi(constructor_abi, args)[2:]  # No 0x
    else:
        constructor_abi = get_constructor_abi(contract.abi)
        kwargs = kwargs or {}
        arguments = merge_args_and_kwargs(constructor_abi, [], kwargs)
        # deploy_data = add_0x_prefix(
        #    contract._encode_abi(constructor_abi, arguments)
        #)

        # TODO: Looks like recent Web3.py ABI change
        deploy_data = encode_abi(contract.web3, constructor_abi, arguments)
        return deploy_data


def getLogs(self,
    argument_filters=None,
    fromBlock=None,
    toBlock="latest",
    address=None,
    topics=None):
    """Get events using eth_getLogs API.

    This is a stateless method, as opposite to createFilter.
    It can be safely called against nodes which do not provide eth_newFilter API, like Infura.

    :param argument_filters:
    :param fromBlock:
    :param toBlock:
    :param address:
    :param topics:
    :return:
    """

    if fromBlock is None:
        raise TypeError("Missing mandatory keyword argument to getLogs: fromBlock")

    abi = self._get_event_abi()

    argument_filters = dict()

    _filters = dict(**argument_filters)

    # Construct JSON-RPC raw filter presentation based on human readable Python descriptions
    # Namely, convert event names to their keccak signatures
    data_filter_set, event_filter_params = construct_event_filter_params(
        abi,
        contract_address=self.address,
        argument_filters=_filters,
        fromBlock=fromBlock,
        toBlock=toBlock,
        address=address,
        topics=topics,
    )

    # Call JSON-RPC API
    logs = self.web3.eth.getLogs(event_filter_params)

    # Convert raw binary data to Python proxy objects as described by ABI
    for entry in logs:
        yield get_event_data(abi, entry)


def priv_key_to_address(private_key):
    from eth_account import Account
    acc = Account.privateKeyToAccount(private_key)
    return acc.address


def _link_bytecode(dbession, bytecode, link_references):
    """
    Return the fully linked contract bytecode.

    Note: This *must* use `get_contract` and **not** `get_contract_address`
    for resolution of link dependencies.  If it merely uses
    `get_contract_address` then the bytecode of sub-dependencies is not
    verified.
    """
    from sto.ethereum.linking import link_bytecode
    resolved_link_references = tuple(
        (
            link_reference,
            get_contract_deployed_tx(dbession, link_reference['name']).contract_address
        )
        for link_reference
        in link_references
    )

    linked_bytecode = link_bytecode(bytecode, resolved_link_references)

    return linked_bytecode


def deploy_contract(config, contract_name, constructor_args=()):
    tx = get_contract_deployed_tx(config.dbsession, contract_name)
    if tx:
        config.logger.error(
            'contract already deployed at address: {}'.format(tx.contract_address)
        )
        return

    from sto.ethereum.txservice import EthereumStoredTXService
    from sto.models.implementation import BroadcastAccount, PreparedTransaction

    assert is_ethereum_network(config.network)

    check_good_private_key(config.ethereum_private_key)

    abi = get_abi(config.ethereum_abi_file)

    for dependency in abi[contract_name]['ordered_full_dependencies']:
        deploy_contract(config, dependency, None)

    abi[contract_name]['bytecode'] = _link_bytecode(
        config.dbsession,
        abi[contract_name]['bytecode'],
        abi[contract_name]['linkrefs']
    )
    abi[contract_name]['bytecode_runtime'] = _link_bytecode(
        config.dbsession,
        abi[contract_name]['bytecode_runtime'],
        abi[contract_name]['linkrefs_runtime'],
    )


    web3 = create_web3(config.ethereum_node_url)
    service = EthereumStoredTXService(
        config.network,
        config.dbsession,
        web3,
        config.ethereum_private_key,
        config.ethereum_gas_price,
        config.ethereum_gas_limit,
        BroadcastAccount,
        PreparedTransaction
    )
    note = "Deploying contract {}".format(contract_name)
    service.deploy_contract(
        contract_name=contract_name,
        abi=abi,
        note=note,
        constructor_args=constructor_args
    )
    # Write database
    dbsession = config.dbsession
    dbsession.commit()
    # deploy on ethereum network
    broadcast(config)


def broadcast(config):
    # extracted this out as a separate method so that
    # this code can be re used elsewhere
    assert is_ethereum_network(config.network)

    logger = config.logger

    from sto.ethereum.broadcast import broadcast as _broadcast

    dbsession = config.dbsession

    txs = _broadcast(
        logger,
        dbsession,
        config.network,
        ethereum_node_url=config.ethereum_node_url,
        ethereum_private_key=config.ethereum_private_key,
        ethereum_gas_limit=config.ethereum_gas_limit,
        ethereum_gas_price=config.ethereum_gas_price
    )

    if txs:
        from sto.ethereum.txservice import EthereumStoredTXService
        EthereumStoredTXService.print_transactions(txs)
        logger.info("Run %ssto tx-update%s to monitor your transaction propagation status", colorama.Fore.LIGHTCYAN_EX,
                    colorama.Fore.RESET)

    # Write database
    dbsession.commit()


def deploy_contract_on_eth_network(
        web3,
        abi,
        bytecode,
        bytecode_runtime,
        private_key,
        ethereum_gas_limit,
        ethereum_gas_price,
        constructor_args
):
    from web3.middleware.signing import construct_sign_and_send_raw_middleware
    # the following code helps deploying using infura
    web3.middleware_stack.add(construct_sign_and_send_raw_middleware(private_key))

    contract = web3.eth.contract(
        abi=abi,
        bytecode=bytecode,
        bytecode_runtime=bytecode_runtime
    )
    tx_kwargs = {
        'from': priv_key_to_address(private_key)
    }
    if ethereum_gas_limit:
        tx_kwargs['gas'] = ethereum_gas_limit
    if ethereum_gas_price:
        tx_kwargs['gasPrice'] = ethereum_gas_price

    tx_hash = contract.constructor(*constructor_args).transact(tx_kwargs)
    receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    assert receipt['status'] == 1, "failed to deploy contract"
    return receipt['contractAddress']


def get_contract_deployed_tx(dbsession, contract_name):
    from sto.models.implementation import PreparedTransaction
    return dbsession.query(PreparedTransaction).filter(
        and_(
            PreparedTransaction.contract_deployment == True,
            PreparedTransaction.filter_by_contract_name(contract_name)
        )
    ).first()


def whitelist_kyc_address(config, address):
    from sto.ethereum.txservice import EthereumStoredTXService
    from sto.models.implementation import BroadcastAccount, PreparedTransaction

    tx = get_contract_deployed_tx(config.dbsession, 'BasicKYC')
    if not tx:
        raise Exception(
            'BasicKyc contract is not deployed. '
            'invoke command kyc_deploy to deploy the smart contract'
        )

    web3 = create_web3(config.ethereum_node_url)

    service = EthereumStoredTXService(
        config.network,
        config.dbsession,
        web3,
        config.ethereum_private_key,
        config.ethereum_gas_price,
        config.ethereum_gas_limit,
        BroadcastAccount,
        PreparedTransaction
    )
    abi = get_abi(config.ethereum_abi_file)

    service.interact_with_contract(
        contract_name='BasicKYC',
        abi=abi,
        address=tx.contract_address,
        note='whitelisting address {0}'.format(address),
        func_name='whitelistUser',
        args={'who': address, 'status': True}
    )
    broadcast(config)


def get_contract_factory_by_name(tx_service, ethereum_abi_file, dbsession, contract_name):
    tx = get_contract_deployed_tx(dbsession, contract_name)
    abi = get_abi(ethereum_abi_file)
    return tx_service.get_contract_proxy(
        contract_name=contract_name,
        abi=abi,
        address=tx.contract_address
    )
