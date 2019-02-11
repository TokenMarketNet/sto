import pytest

from sto.distribution import read_csv
from sto.ethereum.issuance import contract_status
from sto.ethereum.status import update_status
from sto.ethereum.tokenscan import token_scan
from sto.generic.captable import generate_cap_table, print_cap_table
from sto.models.implementation import TokenScanStatus, TokenHolderAccount
from sto.identityprovider import NullIdentityProvider
from sto.cli.main import cli


@pytest.fixture(params=['unrestricted', 'restricted'])
def sample_token(
        logger,
        dbsession,
        web3,
        private_key_hex,
        sample_csv_file,
        db_path,
        click_runner,
        get_contract_deployed_tx,
        kyc_contract,
        monkeypatch_get_contract_deployed_tx,
        request
):
    """Create a security token used in these tests."""
    if request.param == 'restricted':
        from sto.ethereum.utils import priv_key_to_address
        # whitelist owner
        result = click_runner.invoke(
            cli,
            [
                '--database-file', db_path,
                '--ethereum-private-key', private_key_hex,
                '--ethereum-gas-limit', 999999999,
                'kyc-manage',
                '--whitelist-address', priv_key_to_address(private_key_hex)
            ]
        )
        assert result.exit_code == 0

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
            '--transfer-restriction', request.param
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
def scanned_distribution(logger, dbsession, web3, private_key_hex, sample_csv_file, sample_token, click_runner, db_path, monkeypatch_create_web3):
    """Create some sample transactions so we can scan the token holder balances."""

    token_address = sample_token

    entries = read_csv(logger, sample_csv_file)
    for entry in entries:
        # whitelist owner
        result = click_runner.invoke(
            cli,
            [
                '--database-file', db_path,
                '--ethereum-private-key', private_key_hex,
                '--ethereum-gas-limit', 999999999,
                'kyc-manage',
                '--whitelist-address', entry.address
            ]
        )
        assert result.exit_code == 0

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


def test_cap_table_formats(logger, dbsession, network, scanned_distribution, web3):
    """We format cap tables with different orderings."""

    identity_provider = NullIdentityProvider()

    token_address = scanned_distribution
    for sort_direction in ["asc", "desc"]:
        for sort_order in ["address", "name", "balance", "updated"]:
            generate_cap_table(
                logger,
                dbsession,
                token_address,
                order_by=sort_order,
                identity_provider=identity_provider,
                order_direction=sort_direction,
                include_empty=False,
                TokenScanStatus=TokenScanStatus,
                TokenHolderAccount=TokenHolderAccount,
            )


def test_cap_table_printer(logger, dbsession, network, scanned_distribution, web3):
    """We print cap tables with different orderings."""

    identity_provider = NullIdentityProvider()

    token_address = scanned_distribution
    table = generate_cap_table(
        logger,
        dbsession,
        token_address,
        order_by="balance",
        identity_provider=identity_provider,
        include_empty=False,
        order_direction="desc",
        TokenScanStatus=TokenScanStatus,
        TokenHolderAccount=TokenHolderAccount
        )
    print_cap_table(table, max_entries=1000, accuracy=2)





