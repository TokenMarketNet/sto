import pytest

from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.cli.main import cli
from sto.ethereum.utils import get_abi, priv_key_to_address


@pytest.fixture
def deploy(click_runner, db_path, private_key_hex):
    import click
    from sto.ethereum.utils import deploy_contract

    def _deploy_contract(name, contract_args={}):
        @cli.command(name="contract-deploy")
        @click.option('--contract-name', required=True, type=str)
        @click.option('--args', required=True, type=dict)
        @click.pass_obj
        def contract_deploy(config, contract_name, args):
            deploy_contract(config, contract_name, constructor_args=args)

        result = click_runner.invoke(
            cli,
            [
                '--database-file', db_path,
                '--ethereum-private-key', private_key_hex,
                '--ethereum-gas-limit', 999999999,
                'contract-deploy',
                '--contract-name', name,
                '--args', contract_args,
            ]
        )
        assert result.exit_code == 0
    return _deploy_contract


@pytest.fixture
def security_token(deploy, dbsession, monkeypatch_get_contract_deployed_tx, get_contract_deployed_tx):
    args = {
        "_name": "SecurityToken",
        "_symbol": "SEC",
        "_url": "http://tokenmarket.net/"
    }
    deploy('SecurityToken', args)
    tx = get_contract_deployed_tx(dbsession, 'SecurityToken')
    return tx.contract_address


@pytest.fixture
def test_token_name():
    return "CrowdsaleToken"


@pytest.fixture
def execute_contract_function(click_runner, db_path, private_key_hex, web3, get_contract_deployed_tx, dbsession):
    import click

    def _execute_contract(contract_name, contract_function_name, args):
        @cli.command(name="contract-execute")
        @click.option('--contract-name', required=True, type=str)
        @click.option('--contract-function-name', required=True, type=str)
        @click.option('--args', required=True, type=dict)
        @click.pass_obj
        def _execute(config, contract_name, contract_function_name, args):
            from sto.ethereum.txservice import EthereumStoredTXService
            from sto.models.implementation import BroadcastAccount, PreparedTransaction
            from sto.ethereum.utils import broadcast

            service = EthereumStoredTXService(
                config.network,
                config.dbsession,
                web3,
                config.ethereum_private_key,
                config.ethereum_gas_price,
                config.ethereum_gas_limit,
                BroadcastAccount,
                PreparedTransaction
            )
            abi = get_abi(None)
            tx = get_contract_deployed_tx(dbsession, contract_name)
            service.interact_with_contract(
                contract_name, abi, tx.contract_address, '', contract_function_name, args
            )
            broadcast(config)
        result = click_runner.invoke(
            cli,
            [
                '--database-file', db_path,
                '--ethereum-private-key', private_key_hex,
                '--ethereum-gas-limit', 999999999,
                'contract-execute',
                '--contract-name', contract_name,
                '--contract-function-name', contract_function_name,
                '--args', args,
            ]
        )
        assert result.exit_code == 0
    return _execute_contract


@pytest.fixture
def test_token(
        deploy,
        dbsession,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        test_token_name,
        web3,
        private_key_hex,
        execute_contract_function
):
    args = {
        "_name": 'test_token',
        "_symbol": 'TEST',
        "_initialSupply": 900000000,
        "_decimals": 18,
        "_mintable": True
    }
    deploy(test_token_name, args)
    tx = get_contract_deployed_tx(dbsession, test_token_name)
    execute_contract_function(test_token_name, 'setReleaseAgent', {'addr': priv_key_to_address(private_key_hex)})
    execute_contract_function(test_token_name, 'releaseTokenTransfer', {})
    return tx.contract_address


def test_issuance(logger, dbsession, web3, private_key_hex):
    """Walk through issuance process from top to bottom"""

    # Creating transactions
    txs = deploy_token_contracts(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_abi_file=None,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=99999999,
        ethereum_gas_price=None,
        name="Moo Corp",
        symbol="MOO",
        url="https://tokenmarket.net",
        amount=9999,
        transfer_restriction="unrestricted"
    )
    assert len(txs) == 4

    # Send transactions to emphmereal test chain
    txs = broadcast(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
    )
    assert len(txs) == 4

    # Check they got mined
    txs = update_status(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
    )
    assert len(txs) == 4
    for tx in txs:  # type: PreparedTransaction
        assert tx.result_transaction_success

    token_address = txs[0].contract_address

    # Check that we can view the token status
    status = contract_status(
        logger,
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
    txs = deploy_token_contracts(
       logger, dbsession, "testing", web3,
       ethereum_abi_file=None,
       ethereum_private_key=private_key_hex,
       ethereum_gas_limit=99999999,
       ethereum_gas_price=None,
       name="Moo Corp",
       symbol="MOO",
       url="https://tokenmarket.net",
       amount=9999,
       transfer_restriction="unrestricted"
    )

    token_address = txs[0].contract_address

    # Deploy contract transactions to emphmereal test chain
    broadcast(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
    )

    # Check that we can view the token status
    status = contract_status(
        logger,
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

    new_distributes, old_distributes = distribute_tokens(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_abi_file=None,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
        token_address=token_address,
        dists=entries
    )

    assert new_distributes == 2
    assert old_distributes == 0

    # Check they got mined
    # Send transactions to emphmereal test chain
    txs = broadcast(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
    )
    # Check they got mined
    txs = update_status(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
    )
    assert len(txs) == 6
    for tx in txs:  # type: PreparedTransaction
        assert tx.result_transaction_success

    # Check that rerun does not recreate txs
    new_distributes, old_distributes = distribute_tokens(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_abi_file=None,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=None,
        ethereum_gas_price=None,
        token_address=token_address,
        dists=entries
    )

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


def test_voting_deploy(
        private_key_hex,
        db_path,
        monkeypatch_create_web3,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        click_runner,
        security_token,
        kyc_contract,
        web3,
        dbsession
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 9999999,
            'voting-deploy',
            '--token-address', security_token,
            '--kyc-address', kyc_contract,
            '--voting-name', 'abcd',
            '--uri', 'http://tokenmarket.net',
            '--type', 0
        ]
    )
    assert result.exit_code == 0
    abi = get_abi(None)['VotingContract']
    tx = get_contract_deployed_tx(dbsession, 'VotingContract')
    contract = web3.eth.contract(address=tx.contract_address, abi=abi['abi'], bytecode=abi['bytecode'])
    assert contract.functions.blockNumber().call() == web3.eth.blockNumber


def test_payout_deploy(
        private_key_hex,
        db_path,
        monkeypatch_create_web3,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        click_runner,
        dbsession,
        web3,
        security_token,
        kyc_contract,
        test_token,
        test_token_name
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 9999999,
            'payout-deploy',
            '--token-address', security_token,
            '--payout-token-address', test_token,
            '--payout-token-name', test_token_name,
            '--kyc-address', kyc_contract,
            '--payout-name', 'Pay X',
            '--uri', 'http://tokenmarket.net',
            '--type', 0
        ]
    )
    assert result.exit_code == 0
    abi = get_abi(None)['PayoutContract']
    tx = get_contract_deployed_tx(dbsession, 'PayoutContract')
    contract = web3.eth.contract(address=tx.contract_address, abi=abi['abi'], bytecode=abi['bytecode'])
    assert contract.functions.blockNumber().call() == web3.eth.blockNumber


def test_payout_deposit(
        private_key_hex,
        db_path,
        monkeypatch_create_web3,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        click_runner,
        dbsession,
        web3,
        security_token,
        kyc_contract,
        test_token,
        test_token_name,
        customer_private_key
):
    abi = get_abi(None)

    # deploy contract
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 9999999,
            'payout-deploy',
            '--token-address', security_token,
            '--payout-token-address', test_token,
            '--payout-token-name', test_token_name,
            '--kyc-address', kyc_contract,
            '--payout-name', 'Pay X',
            '--uri', 'http://tokenmarket.net',
            '--type', 0
        ]
    )
    assert result.exit_code == 0

    test_token_contract = web3.eth.contract(
        address=test_token,
        abi=abi[test_token_name]['abi']
    )

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 9999999,
            'payout-approve',
            '--payout-token-name', test_token_name,
            '--customer-address', priv_key_to_address(customer_private_key),
            '--transfer-value', test_token_contract.functions.balanceOf(priv_key_to_address(private_key_hex)).call()

        ]
    )
    assert result.exit_code == 0

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', customer_private_key,
            '--ethereum-gas-price', 9999999,
            'payout-deposit',
            '--payout-token-name', test_token_name,
        ]
    )
    assert result.exit_code == 0
    initial_balance = test_token_contract.call().balanceOf(priv_key_to_address(private_key_hex))
    payout_contract.functions.act(123).transact({"from": priv_key_to_address(private_key_hex)})
    assert test_token_contract.call().balanceOf(priv_key_to_address(private_key_hex)) > initial_balance
