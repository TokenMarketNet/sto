"""Distribute tokenised shares on Ethereum."""
from decimal import Decimal
from logging import Logger

import colorama
from sto.ethereum.txservice import EthereumStoredTXService

from sto.ethereum.utils import get_abi, check_good_private_key, create_web3
from sto.ethereum.exceptions import BadContractException
from sto.models.broadcastaccount import _PreparedTransaction

from sto.models.implementation import BroadcastAccount, PreparedTransaction
from sqlalchemy.orm import Session
from typing import Union, Optional, List
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput

def distribute_tokens(logger: Logger,
                          dbsession: Session,
                          network: str,
                          ethereum_node_url: Union[str, Web3],
                          ethereum_abi_file: Optional[str],
                          ethereum_private_key: Optional[str],
                          ethereum_gas_limit: Optional[int],
                          ethereum_gas_price: Optional[int],
                          dists: Lisrt[DistributionEntry]) -> List[_PreparedTransaction]:
    """Issue out a new Ethereum token."""

    txs = []

    assert type(amount) == int
    decimals = 18  # Everything else is bad idea

    check_good_private_key(ethereum_private_key)

    abi = get_abi(ethereum_abi_file)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)


    logger.info("Starting creating transactions from nonce %s", service.get_next_nonce())



    logger.info("Prepared transactions for broadcasting for network %s", network)
    return txs
