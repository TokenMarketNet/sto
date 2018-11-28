import json
from os.path import dirname
from pathlib import Path

from corporategovernance.ethereum.utils import get_abi
from ethpm import Package
from ethpm.tools.builder import build, init_manifest, source_inliner


def get_package(ethereum_abi_file, web3) -> Package:
    """Create a dummy ETHPM package object so we can fiddle with the contract linker.


    To rebuild ABI::

        ./dockerized-solc.sh --combined-json=ast,abi,bin --allow-paths=/ contracts/security-token/SecurityToken.sol > contracts.json

    """

    abi = get_abi(ethereum_abi_file)["contracts"]

    # https://py-ethpm.readthedocs.io/en/latest/tools.html#builder

    inliner = source_inliner(abi)

    base_manifest = init_manifest("dummy", "0", manifest_version="2")

    manifest = build(base_manifest, inliner("contracts/security-token/SecurityToken.sol"))

    package = Package(manifest, web3)
    return package




