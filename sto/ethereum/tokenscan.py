from logging import Logger

from sqlalchemy.orm import Session
from typing import Optional

from sto.ethereum.scanner import TokenScanner
from sto.ethereum.utils import get_abi, create_web3

from sto.models.implementation import TokenScanStatus, TokenHolderDelta,TokenHolderLastBalance


def token_scan(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: str,
              ethereum_abi_file: Optional[str],
              token_address: str,
              start_block: Optional[int]=None,
              end_block: Optional[int]=None) -> dict:
    """Command line entry point to scan token network for events.

    By giving a block range in the middle of existing scanned range you can potentially screw up internal accounting.

    :param start_block: Block from where start scanning. If not given start from the first block or minus then of the last scanned block minus ten blocks.
    :param end_block: Block to where stop scanning. If not given scan to the latest mined block.
    :return: Mapping of address -> final amount of all addresses that were touched during the block range
    """

    abi = get_abi(ethereum_abi_file)

    web3 = create_web3(ethereum_node_url)

    scanner = TokenScanner(logger, network, dbsession, web3, abi, token_address, TokenScanStatus, TokenHolderDelta, TokenHolderLastBalance)

    if start_block is None:
        start_block = scanner.get_suggested_scan_start_block()

    if end_block is None:
        end_block = scanner.get_suggested_scan_end_block()

    result = scanner.scan(start_block, end_block)
    return result