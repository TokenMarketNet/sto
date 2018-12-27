import logging
import os

import pytest
from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.ethereum.tokenscan import token_scan
from sto.models.broadcastaccount import _PreparedTransaction
from sto.models.implementation import TokenScanStatus


@pytest.fixture
def sample_token(logger, dbsession, web3, private_key_hex, sample_csv_file):
    """Create some sample transactions so we can scan the token holder balances."""

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

    return token_address


def test_simple_token_balance_scan(logger, dbsession, network, sample_token, web3):
    """See that we probably scan token balances."""

    start_block = 0
    end_block = web3.eth.blockNumber
    all_balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block, end_block)

    correct_result = {
        '0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6': 300 * 10**18,
        '0xDE5bC059aA433D72F25846bdFfe96434b406FA85': 9199 * 10**18,
        '0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2': 500 * 10**18
    }

    # print("All balances:", all_balances)
    assert all_balances == correct_result

    # Read balances from the datbase
    token_status = dbsession.query(TokenScanStatus).filter_by(address=sample_token).one()
    assert token_status.network == "testing"
    assert token_status.get_total_token_holder_count() == 3

    last_balance_a6 = token_status.balances.filter_by(address="0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6").one()
    assert last_balance_a6.get_balance_uint() == 300 * 10**18
    assert last_balance_a6.last_updated_block == 7
    assert last_balance_a6.last_block_updated_at is not None

    last_balance_d2 = token_status.balances.filter_by(address="0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2").one()
    assert last_balance_d2.get_balance_uint() == 500 * 10**18
    assert last_balance_d2.last_updated_block == 8
    assert last_balance_d2.last_block_updated_at is not None

    # Rescan should be ok, yield to same results
    # This will drop data and scan again
    rescanned_all_balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block, end_block)
    assert all_balances == rescanned_all_balances










