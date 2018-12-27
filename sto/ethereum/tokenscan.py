from logging import Logger

from sqlalchemy.orm import Session

from sto.ethereum.scanner import TokenScanner
from sto.ethereum.utils import get_abi, create_web3

from sto.models.implementation import TokenScanStatus, TokenHolderDelta,TokenHolderLastBalance


def token_scan(logger: Logger,
              dbsession: Session,
              network: str,
              ethereum_node_url: str,
              ethereum_abi_file: str,
               token_address: str,
              start_block: int,
              end_block: int) -> dict:
    """Command line entry point to scan token network for events."""

    abi = get_abi(ethereum_abi_file)

    web3 = create_web3(ethereum_node_url)

    scanner = TokenScanner(logger, network, dbsession, web3, abi, token_address, TokenScanStatus, TokenHolderDelta, TokenHolderLastBalance)
    result = scanner.scan(start_block, end_block)
    return result