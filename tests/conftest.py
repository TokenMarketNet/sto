"""Test fixtures to test out security token activities."""
import logging
import sys

import pytest
from eth_utils import to_wei
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sto.models.implementation import Base

from web3 import Web3, EthereumTesterProvider


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
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
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

