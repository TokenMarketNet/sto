"""Test fixtures to test out security token activities."""
import pytest

from corporategovernance.testutils import check_gas
from web3.contract import Contract



@pytest.fixture
def customer(accounts) -> str:
    """Get a customer address."""
    return accounts[1]


@pytest.fixture
def customer_2(accounts) -> str:
    """Get another customer address."""
    return accounts[2]

@pytest.fixture
def team_multisig(accounts) -> str:
    """The team multisig address."""
    return accounts[3]


@pytest.fixture
def announcement_name() -> str:
    return "Announcement 1"

@pytest.fixture
def announcement_uri() -> str:
    return "https://tokenmarket.net/"

@pytest.fixture
def announcement_type() -> int:
    return 123

@pytest.fixture
def announcement_hash() -> int:
    return 1234


@pytest.fixture
def announcement(chain, team_multisig, announcement_name, announcement_uri, announcement_type, announcement_hash) -> Contract:
    """Create a bogus announcement for testing"""

    args = [announcement_name, announcement_uri, announcement_type, announcement_hash]

    tx = {
        "from": team_multisig
    }

    contract, hash_ = chain.provider.deploy_contract('BogusAnnouncement', deploy_args=args, deploy_transaction=tx)


    check_gas(chain, hash_)

    assert removeNonPrintable(contract.call().announcementName()) == announcement_name
    assert removeNonPrintable(contract.call().announcementURI()) == announcement_uri
    assert contract.call().announcementType() == announcement_type

    return contract


@pytest.fixture
def receiver(chain, team_multisig) -> Contract:
    """Create the receiver contract for callback testing."""

    tx = {
        "from": team_multisig
    }

    contract, hash_ = chain.provider.deploy_contract('MockERC677Receiver', deploy_transaction=tx)
    return contract


@pytest.fixture
def failsafetester(chain, team_multisig) -> Contract:
    """Create a contract for testing the failsafe."""

    tx = {
        "from": team_multisig
    }

    contract, hash_ = chain.provider.deploy_contract('TestCheckpointFailsafe', deploy_transaction=tx)
    return contract

@pytest.fixture
def security_token_name() -> str:
    return "SecurityToken"


@pytest.fixture
def security_token_symbol() -> str:
    return "SEC"


@pytest.fixture
def security_token_initial_supply() -> str:
    return 999999999000000000000000000

@pytest.fixture
def zero_address() -> str:
    return "0x0000000000000000000000000000000000000000"


#
# ERC-20 fixtures
#

@pytest.fixture
def security_token_verifier(chain, team_multisig) -> Contract:
    """Create the transaction verifier contract."""

    tx = {
        "from": team_multisig
    }

    contract, hash_ = chain.provider.deploy_contract('MockSecurityTransferAgent', deploy_transaction=tx)

    check_gas(chain, hash_)

    return contract

@pytest.fixture
def security_token(chain, team_multisig, security_token_name, security_token_symbol, security_token_initial_supply) -> Contract:
    """Create the token contract."""

    args = [security_token_name, security_token_symbol]  # Owner set

    tx = {
        "from": team_multisig
    }

    contract, hash_ = chain.provider.deploy_contract('SecurityToken', deploy_args=args, deploy_transaction=tx)

    check_gas(chain, hash_)

    check_gas(chain, contract.transact(tx).addAddressToWhitelist(team_multisig))
    check_gas(chain, contract.transact(tx).issueTokens(security_token_initial_supply))

    assert contract.call().totalSupply() == security_token_initial_supply
    assert contract.call().balanceOf(team_multisig) == security_token_initial_supply

    return contract

