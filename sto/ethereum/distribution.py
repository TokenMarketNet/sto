"""Distribute tokenised shares on Ethereum."""
from decimal import Decimal
from logging import Logger

import colorama
from tqdm import tqdm

from sto.distribution import DistributionEntry
from sto.ethereum.txservice import EthereumStoredTXService

from sto.ethereum.utils import get_abi, check_good_private_key, create_web3
from sto.ethereum.exceptions import BadContractException
from sto.models.broadcastaccount import _PreparedTransaction

from sto.models.implementation import BroadcastAccount, PreparedTransaction
from sqlalchemy.orm import Session
from typing import Union, Optional, List, Tuple
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput


class NotEnoughTokens(Exception):
    pass



def distribute_tokens(logger: Logger,
                          dbsession: Session,
                          network: str,
                          ethereum_node_url: Union[str, Web3],
                          ethereum_abi_file: Optional[str],
                          ethereum_private_key: Optional[str],
                          ethereum_gas_limit: Optional[int],
                          ethereum_gas_price: Optional[int],
                          token_address: str,
                          dists: List[DistributionEntry]) -> Tuple[int, int]:
    """Sends tokens to their first owners in primary markets."""

    check_good_private_key(ethereum_private_key)

    abi = get_abi(ethereum_abi_file)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    logger.info("Starting creating distribution transactions for %s token from nonce %s", token_address, service.get_next_nonce())

    total = sum([dist.amount * 10**18 for dist in dists])

    available = service.get_raw_token_balance(token_address, abi)
    if total > available:
        raise NotEnoughTokens("Not enough tokens for distribution. Account {} has {} raw token balance, needed {}".format(service.get_or_create_broadcast_account().address, available, total))

    new_distributes = old_distributes = 0

    for d in tqdm(dists):
        if not service.is_distributed(d.external_id, token_address):
            # Going to tx queue
            raw_amount = int(d.amount * 10**18)
            note = "Distributing tokens, raw amount: {}".format(raw_amount)
            service.distribute_tokens(d.external_id, d.address, raw_amount, token_address, abi, note)
            new_distributes += 1
        else:
            # CSV reimports
            old_distributes += 1

    logger.info("Prepared transactions for broadcasting for network %s", network)
    return new_distributes, old_distributes



def distribute_single(logger: Logger,
                          dbsession: Session,
                          network: str,
                          ethereum_node_url: Union[str, Web3],
                          ethereum_abi_file: Optional[str],
                          ethereum_private_key: Optional[str],
                          ethereum_gas_limit: Optional[int],
                          ethereum_gas_price: Optional[int],
                          token_address: str,
                          ext_id: str,
                          email: str,
                          name: str,
                          to_address: str,
                          amount: Decimal) -> bool:
    """Send out a single transfer.

    :return: True if a new tx for broadcasting was created
    """

    assert isinstance(amount, Decimal)
    d = DistributionEntry(ext_id, email, name, to_address, amount)

    check_good_private_key(ethereum_private_key)

    abi = get_abi(ethereum_abi_file)

    web3 = create_web3(ethereum_node_url)

    service = EthereumStoredTXService(network, dbsession, web3, ethereum_private_key, ethereum_gas_price, ethereum_gas_limit, BroadcastAccount, PreparedTransaction)

    logger.info("Starting creating distribution transactions for %s token from nonce %s", token_address, service.get_next_nonce())

    total = d.amount * 10**18

    available = service.get_raw_token_balance(token_address, abi)
    if total > available:
        raise NotEnoughTokens("Not enough tokens for distribution. Account {} has {} raw token balance, needed {}".format(service.get_or_create_broadcast_account().address, available, total))

    if not service.is_distributed(d.external_id, token_address):
        # Going to tx queue
        raw_amount = int(d.amount * 10**18)
        note = "Distributing tokens, raw amount: {}".format(raw_amount)
        service.distribute_tokens(d.external_id, d.address, raw_amount, token_address, abi, note)
        logger.info("New broadcast has been created")
        return True
    else:
        logger.error("Already distributed")
        return False

