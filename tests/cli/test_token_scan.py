import logging
import os

import pytest
from web3.contract import Contract

from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens, distribute_single
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.ethereum.tokenscan import token_scan
from sto.ethereum.utils import get_abi
from sto.models.broadcastaccount import _PreparedTransaction
from sto.models.implementation import TokenScanStatus


@pytest.fixture
def test_account_1(web3_test_provider):
    """Web3 account hosted in testnet"""
    return web3_test_provider.ethereum_tester.get_accounts()[1]


@pytest.fixture
def test_account_2(web3_test_provider):
    """Web3 account hosted in testnet"""
    return web3_test_provider.ethereum_tester.get_accounts()[2]


@pytest.fixture
def test_account_3(web3_test_provider):
    """Web3 account hosted in testnet"""
    return web3_test_provider.ethereum_tester.get_accounts()[3]


@pytest.fixture
def sample_token(logger, dbsession, web3, private_key_hex, sample_csv_file):
    """Create a security token used in these tests."""

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

    return token_address


@pytest.fixture
def sample_distribution(logger, dbsession, web3, private_key_hex, sample_csv_file, sample_token):
    """Create some sample transactions so we can scan the token holder balances."""

    token_address = sample_token

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


@pytest.fixture
def token_contract(sample_token, web3) -> Contract:
    """Proxied ABI to the deployed SecurityToken token contract."""

    contract_name = "SecurityToken"

    abi = get_abi(None)

    abi_data = abi[contract_name]

    contract_class = Contract.factory(
        web3=web3,
        abi=abi_data["abi"],
        bytecode=abi_data["bytecode"],
        bytecode_runtime=abi_data["bytecode_runtime"],
    )

    return contract_class(address=sample_token)


_ext_id_counter = 0

def send_issuer_tokens(logger, dbsession, web3, private_key_hex, token_address, to_address, amount):
    """Send tokens to a receiver."""
    global _ext_id_counter

    _ext_id_counter += 1
    ext_id = str(_ext_id_counter)

    result = distribute_single(logger,
             dbsession,
             "testing",
             web3,
             ethereum_abi_file=None,
             ethereum_private_key=private_key_hex,
             ethereum_gas_limit=None,
             ethereum_gas_price=None,
             token_address=token_address,
             to_address=to_address,
             ext_id=ext_id,
             name=to_address[0:6],
             email="{}@example.com".format(to_address[0:6]),
             amount=amount)

    assert result

    broadcast(logger,
              dbsession,
              "testing",
              web3,
              ethereum_private_key=private_key_hex,
              ethereum_gas_limit=None,
              ethereum_gas_price=None,
              )


def test_simple_token_balance_scan(logger, dbsession, network, sample_distribution, web3):
    """See that we probably scan token balances."""

    token_address = sample_distribution

    start_block = 1
    end_block = web3.eth.blockNumber
    all_balances = token_scan(logger, dbsession, network, web3, None, token_address, start_block, end_block)

    correct_result = {
        '0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6': 300 * 10**18,
        '0xDE5bC059aA433D72F25846bdFfe96434b406FA85': 9199 * 10**18,
        '0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2': 500 * 10**18
    }

    # print("All balances:", all_balances)
    assert all_balances == correct_result

    # Read balances from the datbase
    token_status = dbsession.query(TokenScanStatus).filter_by(address=token_address).one()
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
    rescanned_all_balances = token_scan(logger, dbsession, network, web3, None, token_address, start_block, end_block)
    assert all_balances == rescanned_all_balances

    assert token_status.start_block == 1
    assert token_status.end_block == 8


def test_token_scan_incremental(logger, dbsession, network, private_key_hex, sample_token, web3, test_account_1, test_account_2, test_account_3, token_contract):
    """Call token scan repeatly and see we get new events in."""

    token_address = sample_token
    send_issuer_tokens(logger, dbsession, web3, private_key_hex, token_address, test_account_1, 101)

    # Run incremental scan
    balances = token_scan(logger, dbsession, network, web3, None, sample_token)
    correct_result = {
        '0xDE5bC059aA433D72F25846bdFfe96434b406FA85': 9898 * 10**18,
        test_account_1: 101 * 10**18
    }
    assert balances == correct_result

    # Issuer distributes some more tokens
    start_block = web3.eth.blockNumber + 1
    send_issuer_tokens(logger, dbsession, web3, private_key_hex, token_address, test_account_2, 333)
    end_block = web3.eth.blockNumber
    balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block, end_block)
    correct_result = {
        '0xDE5bC059aA433D72F25846bdFfe96434b406FA85': 9565 * 10**18,
        test_account_2: 333 * 10**18
    }
    assert balances == correct_result

    # Account 1 send some tokens to account 3
    start_block = web3.eth.blockNumber + 1
    token_contract.functions.transfer(test_account_3, 51*10**18).transact({"from": test_account_1})
    end_block = web3.eth.blockNumber
    balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block, end_block)
    correct_result = {
        test_account_1: 50 * 10**18,
        test_account_3: 51 * 10**18,
    }
    assert balances == correct_result

    # Account 1 empties itself, send all remaining tokens to account 3
    start_block = web3.eth.blockNumber + 1
    token_contract.functions.transfer(test_account_3, 50*10**18).transact({"from": test_account_1})
    end_block = web3.eth.blockNumber
    balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block, end_block)
    correct_result = {
        test_account_1: 0 * 10**18,
        test_account_3: 101 * 10**18,
    }
    assert balances == correct_result

    # We have final token holder counts
    token_status = dbsession.query(TokenScanStatus).filter_by(address=token_address).one()

    assert token_status.get_total_token_holder_count() == 3  # issuer, test_account_2, test_account_3
    assert token_status.get_total_token_holder_count(include_empty=True) == 4  # issuer, test_accont_1, test_account_2, test_account_3

    # Do a full scan from the scratch to see the results look ok
    #<Token:0x890042E3d93aC10A426c7ac9e96ED6416B0cC616, holder:0xDE5bC059aA433D72F25846bdFfe96434b406FA85, updated at:8, balance:9565000000000000000000>
    #<Token:0x890042E3d93aC10A426c7ac9e96ED6416B0cC616, holder:0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF, updated at:10, balance:0>
    #<Token:0x890042E3d93aC10A426c7ac9e96ED6416B0cC616, holder:0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69, updated at:8, balance:333000000000000000000>
    #<Token:0x890042E3d93aC10A426c7ac9e96ED6416B0cC616, holder:0x1efF47bc3a10a45D4B230B5d10E37751FE6AA718, updated at:10, balance:101000000000000000000>

    # Check that result match when start from the beginning
    balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block=1, end_block=web3.eth.blockNumber)
    correct_result = {
        '0xDE5bC059aA433D72F25846bdFfe96434b406FA85': 9565 * 10**18,
        test_account_1: 0,
        test_account_2: 333 * 10**18,
        test_account_3: 101 * 10**18,
    }
    assert balances == correct_result

    # Check that result match when start from the middle
    balances = token_scan(logger, dbsession, network, web3, None, sample_token, start_block=8, end_block=web3.eth.blockNumber)
    correct_result = {
        '0xDE5bC059aA433D72F25846bdFfe96434b406FA85': 9565 * 10**18,
        test_account_1: 0,
        test_account_2: 333 * 10**18,
        test_account_3: 101 * 10**18,
    }
    assert balances == correct_result
















