import logging
import os

import pytest
from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.models.broadcastaccount import _PreparedTransaction


def test_issuance(logger, dbsession, web3, private_key_hex):
    """Walk through issuance process from top to bottom"""

    # Creating transactions
    txs = deploy_token_contracts(logger, dbsession, "testing", web3,
                           ethereum_abi_file=None,
                           ethereum_private_key=private_key_hex,
                           ethereum_gas_limit=None,
                           ethereum_gas_price=None,
                           name="Moo Corp",
                           symbol="MOO",
                           amount=9999,
                           transfer_restriction="unrestricted")
    assert len(txs) == 5

    # Send transactions to emphmereal test chain
    txs = broadcast(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   )
    assert len(txs) == 5

    # Check they got mined
    txs = update_status(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   )
    assert len(txs) == 5
    for tx in txs:  # type: PreparedTransaction
        assert tx.result_transaction_success

    token_address = txs[0].contract_address

    # Check that we can view the token status
    status = contract_status(logger,
                    dbsession,
                    "testing",
                    web3,
                    ethereum_abi_file=None,
                    ethereum_private_key=private_key_hex,
                    ethereum_gas_limit=None,
                    ethereum_gas_price=None,
                    token_contract=token_address,
                    )

    assert status["name"] == "Moo Corp"
    assert status["totalSupply"] == 9999 * 10**18
    assert status["totalSupply"] == status["broadcastBalance"]


def test_distribute(logger, dbsession, web3, private_key_hex, sample_csv_file):
    """Distribute tokens."""

    # Creating transactions
    txs = deploy_token_contracts(logger, dbsession, "testing", web3,
                           ethereum_abi_file=None,
                           ethereum_private_key=private_key_hex,
                           ethereum_gas_limit=None,
                           ethereum_gas_price=None,
                           name="Moo Corp",
                           symbol="MOO",
                           amount=9999,
                           transfer_restriction="unrestricted")

    token_address = txs[0].contract_address

    # Deploy contract transactions to emphmereal test chain
    broadcast(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   )

    # Check that we can view the token status
    status = contract_status(logger,
                             dbsession,
                             "testing",
                             web3,
                             ethereum_abi_file=None,
                             ethereum_private_key=private_key_hex,
                             ethereum_gas_limit=None,
                             ethereum_gas_price=None,
                             token_contract=token_address,
                             )

    assert status["name"] == "Moo Corp"
    assert status["totalSupply"] == 9999 * 10 ** 18

    entries = read_csv(logger, sample_csv_file)

    new_distributes, old_distributes = distribute_tokens(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_abi_file=None,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   token_address=token_address,
                   dists=entries)

    assert new_distributes == 2
    assert old_distributes == 0

    # Check they got mined
    # Send transactions to emphmereal test chain
    txs = broadcast(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   )
    # Check they got mined
    txs = update_status(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   )
    assert len(txs) == 7
    for tx in txs:  # type: PreparedTransaction
        assert tx.result_transaction_success

    # Check that rerun does not recreate txs
    new_distributes, old_distributes = distribute_tokens(logger,
                    dbsession,
                    "testing",
                    web3,
                   ethereum_abi_file=None,
                   ethereum_private_key=private_key_hex,
                   ethereum_gas_limit=None,
                   ethereum_gas_price=None,
                   token_address=token_address,
                   dists=entries)

    assert new_distributes == 0
    assert old_distributes == 2








