"""Issuing out tokenised shares."""
from logging import Logger

from corporategovernance.txservice import TransactionService
from web3 import Web3
from web3.contract import Contract

class NoNamedContract(Exception):
    pass


def issue_ethereum(logger: Logger, web3: Web3, abi: dict, name: str, symbol: str, amount: int, contract_name: str, txservice: TransactionService):
    """Issue out a new Ethereum token."""

    assert isinstance(abi, dict)

    abi_data = abi.get(contract_name)
    if not abi_data:
        raise NoNamedContract("Ethereum ABI does not have contract {}".format(contract_name))

    contract_class = Contract.factory(
        web3=web3,
        abi=abi_data["abi"],
        bytecode=abi_data["bytecode"],
        bytecode_runtime=abi_data["bytecode_runtime"],
        )


