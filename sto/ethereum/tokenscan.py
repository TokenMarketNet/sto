from logging import Logger

import colorama
from sqlalchemy.orm import Session
from typing import Optional

from tqdm import tqdm

from sto.ethereum.scanner import TokenScanner
from sto.ethereum.utils import get_abi, create_web3

from sto.models.implementation import TokenScanStatus, TokenHolderDelta,TokenHolderAccount


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

    scanner = TokenScanner(logger, network, dbsession, web3, abi, token_address, TokenScanStatus, TokenHolderDelta, TokenHolderAccount)

    if start_block is None:
        start_block = scanner.get_suggested_scan_start_block()

    if end_block is None:
        end_block = scanner.get_suggested_scan_end_block()

    last_scanned_block = scanner.get_last_scanned_block()

    status = scanner.get_or_create_status()
    token_name = status.name

    last_block = web3.eth.blockNumber
    logger.info("Scanning token: %s%s%s", colorama.Fore.LIGHTGREEN_EX, token_name, colorama.Fore.RESET)
    logger.info("Current last block for chain %s: %s%s%s", network, colorama.Fore.LIGHTGREEN_EX, last_block, colorama.Fore.RESET)
    logger.info("Scanning blocks: %s%d%s - %s%d%s", colorama.Fore.LIGHTGREEN_EX, start_block, colorama.Fore.RESET, colorama.Fore.LIGHTGREEN_EX, end_block, colorama.Fore.RESET)

    if last_scanned_block:
        logger.info("Last scan ended at block: %s%d%s", colorama.Fore.LIGHTGREEN_EX, last_scanned_block, colorama.Fore.RESET)

    total = end_block - start_block
    with tqdm(total=total) as progress_bar:
        def _update_progress(start, end, current, chunk_size):
            progress_bar.set_description("Scanning block: {}, batch size: {}".format(current, chunk_size))
            progress_bar.update(chunk_size)

        result = scanner.scan(start_block, end_block, progress_callback=_update_progress)
    return result