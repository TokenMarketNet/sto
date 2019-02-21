import pytest

from sto.distribution import read_csv
from sto.ethereum.issuance import contract_status
from sto.ethereum.status import update_status
from sto.ethereum.tokenscan import token_scan
from sto.generic.captable import generate_cap_table, print_cap_table
from sto.models.implementation import TokenScanStatus, TokenHolderAccount
from sto.identityprovider import NullIdentityProvider
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


def test_payout_distribute(
        monkeypatch_create_web3,
        holders_payout_csv,
        csv_output,
        click_runner,
        db_path,
        private_key_hex,
        security_token
):
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
            '--total-amount', 9999000000000000000000
        ]
    )
    assert result.exit_code == 0
