import web3
from corporategovernance.models.broadcastaccount import _BroadcastAccount, _PreparedTransaction
from eth_account import Account
from sqlalchemy.orm import Session
from typing import Optional
from web3 import Web3
from web3.contract import Contract

from corporategovernance.models.implementation import _BroadcastAccount


class NetworkAndDatabaseNonceOutOfSync(Exception):
    pass


class EthereumStoredTXService:
    """A transaction service that writes entries to a local database before trying to broadcast them to the blockchain."""

    def __init__(self, network: str, dbsession: Session, web3: Web3, private_key_hex: str, gas_price, gas_limit, broadcast_account_model, prepared_tx_model):

        assert isinstance(web3, Web3)

        self.network = network  # "kovan"
        self.dbsession = dbsession
        self.web3 = web3
        self.account = Account.privateKeyToAccount(private_key_hex)

        # SQLAlchemy models, allow caller to supply their own
        self.broadcast_account_model = broadcast_account_model
        self.prepared_tx_model = prepared_tx_model

        self.gas_price = gas_price
        self.gas_limit = gas_limit

    @property
    def address(self):
        return self.account.address

    def get_or_create_broadcast_account(self):
        """
        :return:
        """
        account = self.dbsession.query(self.broadcast_account_model).filter_by(network=self.network, address=self.address).one_or_none()
        if not account:
            account = self.broadcast_account_model(network=self.network, address=self.address)
            self.dbsession.add(account)
            self.dbsession.flush()

        return account

    def get_next_nonce(self):
        broadcast_account = self.get_or_create_broadcast_account()
        return broadcast_account.current_nonce

    def ensure_account_in_sync(self, broadcast_account: _BroadcastAccount):
        """Make sure that our internal nonce and external nonce looks correct."""

        tx_count = self.web3.getTransactionAccont(broadcast_account.address)

        network_nonce = tx_count + 1

        if tx_count != broadcast_account.current_nonce:
            NetworkAndDatabaseNonceOutOfSync("Nonced out of sync. Network: {}, database: {}".format(network_nonce, broadcast_account.current_nonce))

    def allocate_transaction(self,
                             broadcast_account: _BroadcastAccount,
                             receiver: Optional[str],
                             contract_address: Optional[str],
                             contract_deployment: bool,
                             nonce: int,
                             note: str,
                             unsigned_payload: str,
                             gas_price: Optional[int],
                             gas_limit: Optional[int]):
        """Put a transaction to the pending queue of the current broadcast list."""

        assert broadcast_account.current_nonce == nonce
        tx = self.prepared_tx_model()
        tx.nonce = nonce
        tx.human_readable_description = note
        tx.receiver = receiver
        tx.contract_address = contract_address
        tx.gas_price = gas_price
        tx.gas_limit = gas_limit
        tx.contract_deployment = contract_deployment
        tx.unsigned_payload = unsigned_payload
        broadcast_account.txs.append(tx)
        broadcast_account.current_nonce += 1

    def deploy_contract(self, contract_name: str, abi: dict, note: str, constructor_args=None) -> _PreparedTransaction:
        """Deploys a contract."""

        if not constructor_args:
            constructor_args = {}

        abi_data = abi[contract_name]

        contract_class = Contract.factory(
            web3=self.web3,
            abi=abi_data["abi"],
            bytecode=abi_data["bytecode"],
            bytecode_runtime=abi_data["bytecode_runtime"],
            )

        broadcast_account = self.get_or_create_broadcast_account()

        next_nonce = self.get_next_nonce()

        constructed_txn = contract_class.constructor(**constructor_args).buildTransaction({
            'from': self.address,
            'nonce': next_nonce,
            'gas': self.gas_limit,
            'gasPrice': self.gas_price})

        derived_contract_address = None

        self.allocate_transaction(
            broadcast_account=broadcast_account,
            receiver=None,
            contract_address=derived_contract_address,
            contract_deployment=True,
            nonce=next_nonce,
            note=note,
            unsigned_payload=constructed_txn,
            gas_price=self.gas_price,
            gas_limit=self.gas_limit,
        )

    def interact_with_contract(self, contract_name: str, abi: dict, address: str, note: str, func_name: str, args=None, receiver=None) -> _PreparedTransaction:
        """Does a transaction against a contract.."""

        if not args:
            args = {}

        abi_data = abi[contract_name]

        contract_class = Contract.factory(
            web3=self.web3,
            abi=abi_data["abi"],
            bytecode=abi_data["bytecode"],
            bytecode_runtime=abi_data["bytecode_runtime"],
            )

        broadcast_account = self.get_or_create_broadcast_account()

        next_nonce = self.get_next_nonce()

        func = getattr(contract_class.functions, func_name)

        constructed_txn = func(**args).buildTransaction({
            'from': self.address,
            'nonce': next_nonce,
            'gas': self.gas_limit,
            'gasPrice': self.gas_price})

        self.allocate_transaction(
            broadcast_account=broadcast_account,
            receiver=receiver,
            contract_address=address,
            contract_deployment=True,
            nonce=next_nonce,
            note=note,
            unsigned_payload=constructed_txn,
            gas_price=self.gas_price,
            gas_limit=self.gas_limit,
        )











