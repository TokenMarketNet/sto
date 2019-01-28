import logging
import os

import pytest

from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.cli.main import cli
from sto.ethereum.utils import get_abi


@pytest.fixture
def security_token(web3, private_key_hex):
    from sto.ethereum.utils import deploy_contract_on_eth_network, get_abi
    args = ["SecurityToken", "SEC", "http://tokenmarket.net/"]  # Owner set
    abi = get_abi(None)['SecurityToken']

    return deploy_contract_on_eth_network(
        web3,
        abi['abi'],
        abi['bytecode'],
        abi['bytecode_runtime'],
        private_key_hex,
        None,
        None,
        constructor_args=args
    )


@pytest.fixture
def kyc_contract(click_runner, dbsession, db_path, private_key_hex):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            'kyc-deploy'
        ]
    )
    assert result.exit_code == 0
    tx = get_contract_deployed_tx(dbsession, 'BasicKYC')
    return tx.contract_address


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


def test_kyc_deploy(
        dbsession,
        private_key_hex,
        db_path,
        monkeypatch_create_web3,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        web3,
        click_runner
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            'kyc-deploy'
        ]
    )
    assert result.exit_code == 0
    tx = get_contract_deployed_tx(dbsession, 'BasicKYC')
    assert tx.contract_name == 'BasicKYC'
    assert tx.contract_address is not None
    assert web3.eth.getCode(tx.contract_address) not in ['0x', None]


def test_kyc_manage(
        dbsession,
        private_key_hex,
        web3,
        db_path,
        monkeypatch_create_web3,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        click_runner
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            'kyc-deploy'
        ]
    )
    assert result.exit_code == 0
    tx = get_contract_deployed_tx(dbsession, 'BasicKYC')
    abi = get_abi(None)
    kyc_contract = web3.eth.contract(address=tx.contract_address, abi=abi['BasicKYC']['abi'])

    eth_address = web3.eth.account.create().address

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 80000,
            'kyc-manage',
            '--whitelist-address', eth_address
        ]
    )
    assert result.exit_code == 0
    assert kyc_contract.functions.isWhitelisted(eth_address).call() == True
