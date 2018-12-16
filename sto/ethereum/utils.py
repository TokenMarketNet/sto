import binascii
import json
import os

from typing import Optional

import rlp
from eth_abi import encode_abi
from web3 import Web3, HTTPProvider
from web3.contract import Contract
from web3.utils.abi import get_constructor_abi, merge_args_and_kwargs
from web3.utils.normalizers import normalize_address
from eth_utils import keccak, to_checksum_address, to_bytes, is_hex_address, is_checksum_address
from web3.utils.contracts import encode_abi

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
