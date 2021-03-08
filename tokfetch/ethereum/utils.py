import json
import os
from typing import Optional

from eth_abi import encode_abi
from web3 import Web3, HTTPProvider
from web3.contract import Contract

try:
    from web3.utils.abi import get_constructor_abi, merge_args_and_kwargs
    from web3.utils.events import get_event_data
    from web3.utils.filters import construct_event_filter_params
    from web3.utils.contracts import encode_abi
    from web3.middleware import geth_poa_middleware
except ImportError:
    from web3._utils.abi import get_constructor_abi, merge_args_and_kwargs
    from web3._utils.events import get_event_data
    from web3._utils.filters import construct_event_filter_params
    from web3._utils.contracts import encode_abi
    from web3.middleware import geth_poa_middleware

from eth_utils import (
    keccak,
    is_hex_address,
    is_checksum_address,
    to_hex
)


class NoNodeConfigured(Exception):
    pass


class NeedPrivateKey(Exception):
    pass


def check_good_node_url(node_url: str):
    if not node_url:
        raise NoNodeConfigured("You need to give --ethereum-node-url command line option or set it up in a config file")


def get_abi():
    abi_file = os.path.join(os.path.dirname(__file__), "erc20.abi.json")

    with open(abi_file, "rt") as inp:
        return json.load(inp)


def create_web3(url: str) -> Web3:
    """Web3 initializer."""

    if isinstance(url, Web3):
        # Shortcut for testing
        url.middleware_onion.inject(geth_poa_middleware, layer=0)
        return url
    else:
        w3 = Web3(HTTPProvider(url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3


def integer_hash(number: int):
    return int(keccak(number).hex(), 16)


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


def get_constructor_arguments(contract: Contract, args: Optional[list] = None, kwargs: Optional[dict] = None):
    """Get constructor arguments for Etherscan verify.

    https://etherscanio.freshdesk.com/support/solutions/articles/16000053599-contract-verification-constructor-arguments
    """

    # return contract._encode_constructor_data(args=args, kwargs=kwargs)
    constructor_abi = get_constructor_abi(contract.abi)

    # constructor_abi can be none in case of libraries
    if constructor_abi is None:
        return to_hex(contract.bytecode)

    if args is not None:
        return contract.encodeABI(constructor_abi['name'], args)[2:]  # No 0x
    else:
        constructor_abi = get_constructor_abi(contract.abi)
        kwargs = kwargs or {}
        arguments = merge_args_and_kwargs(constructor_abi, [], kwargs)
        # deploy_data = add_0x_prefix(
        #    contract._encode_abi(constructor_abi, arguments)
        # )

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
        abi_codec=self.web3.codec,
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
        yield get_event_data(self.web3.codec, abi, entry)
