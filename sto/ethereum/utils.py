import binascii
import json
import os

from typing import Optional

import rlp
from web3 import Web3, HTTPProvider
from web3.utils.normalizers import normalize_address
from eth_utils import keccak, to_checksum_address, to_bytes


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
        abi_file = os.path.join(os.path.dirname(__file__), "contracts.json")

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
