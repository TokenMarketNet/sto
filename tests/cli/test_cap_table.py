import pytest

from sto.distribution import read_csv
from sto.ethereum.broadcast import broadcast
from sto.ethereum.distribution import distribute_tokens
from sto.ethereum.issuance import deploy_token_contracts, contract_status
from sto.ethereum.status import update_status
from sto.ethereum.tokenscan import token_scan
from sto.generic.captable import generate_cap_table, print_cap_table
from sto.models.implementation import TokenScanStatus, TokenHolderAccount
from sto.identityprovider import NullIdentityProvider


@pytest.fixture
def sample_token(logger, dbsession, web3, private_key_hex, sample_csv_file):
    """Create a security token used in these tests."""

    # Creating transactions
    txs = deploy_token_contracts(
        logger,
        dbsession,
        "testing",
        web3,
        ethereum_abi_file=None,
        ethereum_private_key=private_key_hex,
        ethereum_gas_limit=9999999,
        ethereum_gas_price=None,
        name="Moo Corp",
        symbol="MOO",
        url="https://tokenmarket.net",
        amount=9999,
        transfer_restriction="unrestricted"
    )

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
def scanned_distribution(logger, dbsession, web3, private_key_hex, sample_csv_file, sample_token):
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





