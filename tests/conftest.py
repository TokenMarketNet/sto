"""Test fixtures to test out security token activities."""
import logging

import pytest
from eth_utils import to_wei
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sto.models.implementation import Base

from sto.testutils import check_gas
from web3 import Web3, EthereumTesterProvider
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


@pytest.fixture
def dbsession():
    """We use sqlite in-memory for testing."""

    # https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html
    url = "sqlite+pysqlite:///" + ":memory:"

    engine = create_engine(url, echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    return session


@pytest.fixture
def web3_test_provider():
    return EthereumTesterProvider()


@pytest.fixture
def web3(web3_test_provider):
    return Web3(web3_test_provider)


@pytest.fixture
def logger():
    return logging.getLogger()


@pytest.fixture
def private_key_hex(web3_test_provider, web3):
    """Create a static private key with some ETH balance on it."""
    # accounts = web3_test_provider.ethereum_tester.get_accounts()
    private_key_hex = "3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c8005"

    acc_zero = web3_test_provider.ethereum_tester.get_accounts()[0]  # Accounts with pregenerated balance
    address = web3_test_provider.ethereum_tester.add_account(private_key_hex)
    web3.eth.sendTransaction({"from": acc_zero, "to": address, "value": to_wei(1, "ether")})
    balance = web3.eth.getBalance(address)
    assert balance > 0
    return private_key_hex

