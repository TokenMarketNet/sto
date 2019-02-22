import csv
import pytest

from sto.ethereum.issuance import contract_status
from sto.ethereum.status import update_status
from sto.ethereum.tokenscan import token_scan
from sto.ethereum.utils import priv_key_to_address, get_abi
from sto.cli.main import cli


@pytest.fixture
def sample_token(
        logger,
        dbsession,
        web3,
        private_key_hex,
        sample_csv_file,
        db_path,
        click_runner,
        get_contract_deployed_tx,
        monkeypatch_get_contract_deployed_tx,
        monkeypatch_create_web3
):
    """Create a security token used in these tests."""

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'issue',
            '--name', "Moo Corp",
            '--symbol', "MOO",
            '--url', "https://tokenmarket.net",
            '--amount', 9999,
        ]
    )

    assert result.exit_code == 0
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',

        ]
    )
    assert result.exit_code == 0

    token_address = get_contract_deployed_tx(dbsession, "SecurityToken").contract_address

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
    dbsession.commit()

    return token_address


@pytest.fixture
def scanned_distribution(
        logger,
        dbsession,
        web3,
        private_key_hex,
        sample_csv_file,
        sample_token,
        click_runner,
        db_path,
        monkeypatch_create_web3
):
    """Create some sample transactions so we can scan the token holder balances."""

    token_address = sample_token

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "distribute-multiple",
            '--csv-input', sample_csv_file,
            '--address', token_address
        ]
    )

    assert result.exit_code == 0

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',
        ]
    )
    assert result.exit_code == 0

    # Check they got mined
    # Send transactions to emphmereal test chain
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',

        ]
    )
    assert result.exit_code == 0

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


    # Check that rerun does not recreate txs
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "distribute-multiple",
            '--csv-input', sample_csv_file,
            '--address', token_address
        ]
    )

    assert result.exit_code == 0

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',
        ]
    )
    assert result.exit_code == 0

    token_scan(logger, dbsession, "testing", web3, None, token_address)
    return token_address


@pytest.fixture
def csv_output(tmp_path):
    return str(tmp_path / 'payout.csv')


@pytest.fixture
def holders_payout_csv(
        scanned_distribution,
        monkeypatch_create_web3,
        click_runner,
        db_path,
        private_key_hex,
        csv_output,
        security_token
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "create-holders-payout-csv",
            '--csv-output', csv_output,
            '--token-address', security_token
        ]
    )
    assert result.exit_code == 0


@pytest.fixture
def test_token(
        deploy,
        dbsession,
        monkeypatch_get_contract_deployed_tx,
        get_contract_deployed_tx,
        web3,
        private_key_hex,
        execute_contract_function
):
    args = {
        "_name": "CrowdsaleToken",
        "_symbol": 'TEST',
        "_initialSupply": 9999000000000000000000,
        "_decimals": 18,
        "_mintable": True
    }
    deploy('CrowdsaleToken', args)
    tx = get_contract_deployed_tx(dbsession, 'CrowdsaleToken')
    execute_contract_function('CrowdsaleToken', 'setReleaseAgent', {'addr': priv_key_to_address(private_key_hex)})
    execute_contract_function('CrowdsaleToken', 'releaseTokenTransfer', {})
    return tx.contract_address


def test_create_holders_payout_csv(
        scanned_distribution,
        monkeypatch_create_web3,
        click_runner,
        db_path,
        private_key_hex,
        csv_output,
        security_token
):
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "create-holders-payout-csv",
            '--csv-output', csv_output,
            '--token-address', security_token
        ]
    )
    assert result.exit_code == 0
    with open(csv_output, 'rt') as f:
        reader = csv.reader(f)
        rows = [row for row in reader]
        assert len(rows) == 4


def test_payout_distribute_ether(
        monkeypatch_create_web3,
        holders_payout_csv,
        csv_output,
        click_runner,
        db_path,
        private_key_hex,
        security_token,
        web3,
):
    inital_balance_1 = web3.eth.getBalance('0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6')
    inital_balance_2 = web3.eth.getBalance('0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2')

    total_amount = web3.toWei(100, 'ether')
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            '--ethereum-gas-price', 20000,
            "payout-distribute",
            '--csv-input', csv_output,
            '--security-token-address', security_token,
            '--total-amount', total_amount
        ]
    )
    assert result.exit_code == 0
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',
        ]
    )
    assert result.exit_code == 0

    after_balance_1 = web3.eth.getBalance('0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6')
    after_balance_2 = web3.eth.getBalance('0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2')
    assert after_balance_1 > inital_balance_1
    assert after_balance_2 > inital_balance_2

    assert after_balance_1 == 3000300030003000300
    assert after_balance_2 == 5000500050005000500

    # test csv input re-run
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            '--ethereum-gas-price', 20000,
            "payout-distribute",
            '--csv-input', csv_output,
            '--security-token-address', security_token,
            '--total-amount', total_amount
        ]
    )
    assert result.exit_code == 0
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',
        ]
    )
    assert result.exit_code == 0
    re_run_balance_1 = web3.eth.getBalance('0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6')
    re_run_balance_2 = web3.eth.getBalance('0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2')
    assert after_balance_1 == re_run_balance_1
    assert after_balance_2 == re_run_balance_2


def test_payout_tokens(
        monkeypatch_create_web3,
        holders_payout_csv,
        csv_output,
        click_runner,
        db_path,
        private_key_hex,
        security_token,
        web3,
        test_token,
        get_contract_deployed_tx,
        dbsession,
):
    inital_balance_1 = web3.eth.getBalance('0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6')
    inital_balance_2 = web3.eth.getBalance('0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2')

    total_amount = 1000000000000000000
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            '--ethereum-gas-price', 20000,
            "payout-distribute",
            '--csv-input', csv_output,
            '--security-token-address', security_token,
            '--total-amount', total_amount,
            '--payment-type', 'token',
            '--payout-token-address', test_token
        ]
    )
    assert result.exit_code == 0
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',
        ]
    )
    assert result.exit_code == 0

    tx = get_contract_deployed_tx(dbsession, 'CrowdsaleToken')
    abi = get_abi(None)
    test_token_contract = web3.eth.contract(address=tx.contract_address, abi=abi['CrowdsaleToken']['abi'])

    after_balance_1 = test_token_contract.functions.balanceOf('0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6').call()
    after_balance_2 = test_token_contract.functions.balanceOf('0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2').call()
    assert after_balance_1 > inital_balance_1
    assert after_balance_2 > inital_balance_2


    # test csv input re-run
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            '--ethereum-gas-price', 20000,
            "payout-distribute",
            '--csv-input', csv_output,
            '--security-token-address', security_token,
            '--total-amount', total_amount
        ]
    )
    assert result.exit_code == 0
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',
        ]
    )
    assert result.exit_code == 0

    re_run_balance_1 = test_token_contract.functions.balanceOf('0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6').call()
    re_run_balance_2 = test_token_contract.functions.balanceOf('0xE738f7A6Eb317b8B286c27296cD982445c9D8cd2').call()
    assert after_balance_1 == re_run_balance_1
    assert after_balance_2 == re_run_balance_2
