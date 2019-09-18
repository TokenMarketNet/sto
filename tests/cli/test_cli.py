import pytest

from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.cli.main import cli
from sto.ethereum.utils import get_abi


@pytest.fixture
def kyc_contract(
        click_runner,
        dbsession,
        db_path,
        private_key_hex,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx
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
    return tx.contract_address


@pytest.fixture
def test_token(deploy, dbsession, monkeypatch_get_contract_deployed_tx, get_contract_deployed_tx):
    args = {
        "_name": 'test_token',
        "_symbol": 'TEST',
        "_initialSupply": 900000000,
        "_decimals": 18,
        "_mintable": True
    }
    deploy('CrowdsaleToken', args)
    tx = get_contract_deployed_tx(dbsession, 'CrowdsaleToken')
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
    # TODO: this method is no longer supported but maybe this should be tested
    # some other way?
    #assert kyc_contract.functions.isWhitelisted(eth_address).call() == True


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
            '--ethereum-gas-price', 20,
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
        test_token
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 20,
            'payout-deploy',
            '--token-address', security_token,
            '--payout-token-address', test_token,
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
    test_token_name
):
    abi = get_abi(None)

    # deploy contract
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price',20,
            'payout-deploy',
            '--token-address', security_token,
            '--payout-token-address', test_token,
            '--payout-token-name', test_token_name,
            '--kyc-address', kyc_contract,
            '--payout-name', 'Pay X',
            '--uri', 'http://tokenmarket.net',
            '--type', 0,
            '--options', ["Vested for dividend", ]
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
            '--ethereum-gas-price', 20,
            'payout-approve',
            '--payout-token-name', test_token_name
        ]
    )
    assert result.exit_code == 0
    payout_contract_address = get_contract_deployed_tx(dbsession, 'PayoutContract').contract_address
    payout_contract = web3.eth.contract(
        address=payout_contract_address,
        abi=abi['PayoutContract']['abi']
    )
    initial_balance = test_token_contract.call().balanceOf(payout_contract_address)
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 20,
            'payout-deposit'
        ]
    )
    assert result.exit_code == 0
    assert test_token_contract.functions.balanceOf(payout_contract.address).call() > initial_balance
    # check if payouts happen
    initial_balance = test_token_contract.call().balanceOf(priv_key_to_address(private_key_hex))
    payout_contract.functions.act(123).transact({"from": priv_key_to_address(private_key_hex)})
    # 0x0000000000000000000000000000000000000064 is the default address 100
    assert payout_contract.functions.balanceOf('0x0000000000000000000000000000000000000064').call() == 123
    assert test_token_contract.call().balanceOf(priv_key_to_address(private_key_hex)) > initial_balance


def test_payout_dividends(
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
            '--ethereum-gas-price', 20,
            'payout-deploy',
            '--token-address', security_token,
            '--payout-token-address', test_token,
            '--payout-token-name', test_token_name,
            '--kyc-address', kyc_contract,
            '--payout-name', 'Pay X',
            '--uri', 'http://tokenmarket.net',
            '--type', 0,
            '--options', ["Vested for dividend", ]
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
            '--ethereum-gas-price', 20,
            'payout-approve',
            '--payout-token-name', test_token_name
        ]
    )
    assert result.exit_code == 0
    payout_contract_address = get_contract_deployed_tx(dbsession, 'PayoutContract').contract_address
    payout_contract = web3.eth.contract(
        address=payout_contract_address,
        abi=abi['PayoutContract']['abi']
    )
    initial_balance = test_token_contract.call().balanceOf(payout_contract_address)
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-price', 20,
            'payout-deposit'
        ]
    )
    assert result.exit_code == 0
    assert test_token_contract.functions.balanceOf(payout_contract.address).call() > initial_balance
    # TODO: complete this test
    # check if payouts happen
    # initial_balance = test_token_contract.call().balanceOf(priv_key_to_address(customer_private_key))
    # payout_contract.functions.act(123).transact({"from": priv_key_to_address(customer_private_key)})
    # # 0x0000000000000000000000000000000000000064 is the default address 100
    # assert payout_contract.functions.balanceOf('0x0000000000000000000000000000000000000064').call() == 123
    # assert test_token_contract.call().balanceOf(priv_key_to_address(customer_private_key)) > initial_balance
