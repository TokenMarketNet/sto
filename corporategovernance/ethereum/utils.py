import json
import os

from typing import Optional


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