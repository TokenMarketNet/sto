from sto.ethereum.utils import mk_contract_address
from sto.models.broadcastaccount import _BroadcastAccount, _PreparedTransaction
from sto.models.utils import now
from eth_account import Account
from eth_utils import to_checksum_address

from sqlalchemy.orm import Session, Query
from typing import Optional, Iterable
from web3 import Web3
from web3.contract import Contract

from sto.models.implementation import _BroadcastAccount


class NetworkAndDatabaseNonceOutOfSync(Exception):
    pass


class EthereumStoredTXService:
    """A transaction service that writes entries to a local database before trying to broadcast them to the blockchain."""

    def __init__(self, network: str, dbsession: Session, web3: Web3, private_key_hex: str, gas_price, gas_limit, broadcast_account_model, prepared_tx_model):

        assert isinstance(web3, Web3)

        self.network = network  # "kovan"
        self.dbsession = dbsession
        self.web3 = web3
        self.private_key_hex = private_key_hex
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

        # Some early prototype sanity checks
        assert self.address.startswith("0x")
        assert self.network in ("kovan", "ethereum")

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

        tx_count = self.web3.eth.getTransactionCount(broadcast_account.address)

        if tx_count != broadcast_account.current_nonce:
            NetworkAndDatabaseNonceOutOfSync("Nonced out of sync. Network: {}, database: {}".format(network_nonce, broadcast_account.current_nonce))

    def allocate_transaction(self,
                             broadcast_account: _BroadcastAccount,
                             receiver: Optional[str],
                             contract_address: Optional[str],
                             contract_deployment: bool,
                             nonce: int,
                             note: str,
                             unsigned_payload: dict,
                             gas_price: Optional[int],
                             gas_limit: Optional[int]) -> _PreparedTransaction:
        """Put a transaction to the pending queue of the current broadcast list."""

        if receiver:
            assert receiver.startswith("0x")

        assert contract_deployment in (True, False)

        assert broadcast_account.current_nonce == nonce

        assert type(unsigned_payload) == dict

        tx = self.prepared_tx_model()  # type: _PreparedTransaction
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
        return tx

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

        # Creates a dict for signing
        constructed_txn = contract_class.constructor(**constructor_args).buildTransaction({
            'from': self.address,
            'nonce': next_nonce,
            'gas': self.gas_limit,
            'gasPrice': self.gas_price})


        derived_contract_address = mk_contract_address(self.address, next_nonce)
        derived_contract_address = to_checksum_address(derived_contract_address.lower())

        constructed_txn["to"] = "" # Otherwise database serializer complains about bytes string

        tx = self.allocate_transaction(
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

        self.dbsession.flush()
        return tx

    def interact_with_contract(self, contract_name: str, abi: dict, address: str, note: str, func_name: str, args=None, receiver=None) -> _PreparedTransaction:
        """Does a transaction against a contract."""

        assert address.startswith("0x")

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
            'to': address,
            'from': self.address,
            'nonce': next_nonce,
            'gas': self.gas_limit,
            'gasPrice': self.gas_price})

        tx = self.allocate_transaction(
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
        self.dbsession.flush()
        return tx

    def get_pending_broadcasts(self) -> Query:
        """All transactions that need to be broadcasted."""
        return self.dbsession.query(self.prepared_tx_model).filter_by(txid=None).join(self.broadcast_account_model).filter_by(network=self.network)

    def get_unmined_txs(self) -> Query:
        """All transactions that do not yet have a block assigned."""
        return self.dbsession.query(self.prepared_tx_model).filter_by(self.prepared_tx_model.is_(None)).join(self.broadcast_account_model).filter_by(network=self.network)

    def broadcast(self, txs: Iterable[_PreparedTransaction]):
        """Push transactions to Ethereum network."""
        for tx in txs:
            tx_data = tx.unsigned_payload
            signed = self.web3.eth.account.signTransaction(tx_data, self.private_key_hex)
            tx.txid = signed.hash
            self.web3.sendRawTransaction(signed.rawTransaction)
            tx.broadcasted_at = now()
            yield tx

    def update_status(self, txs: Iterable[_PreparedTransaction]):
        """Update tx status from Etheruem network."""

        for tx in txs:
            assert tx.txid

            # https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
            receipt = self.web3.eth.getTransactionReceipt(tx.txid)
            if receipt:
                tx.result_block_num = receipt["blockNumber"]

                # TODO: Needs smarter Ethreum transaction evaluation
                if receipt["gas"] == receipt["gasUsed"]:
                    tx.result_transaction_success = False
                    tx.result_transaction_reason = "Gas limit exceeded"
                else:
                    tx.result_transaction_success = True

            tx.result_fetched_at = now()
            yield tx

    @classmethod
    def print_transactions(self, txs: Iterable[_PreparedTransaction]):
        """Print transaction status to the console"""

        from tabulate import tabulate # https://bitbucket.org/astanin/python-tabulate
        import colorama # https://pypi.org/project/colorama/

        colorama.init()

        table = []
        for tx in txs:

            status = tx.get_status()
            if status == "waiting":
                status = colorama.Fore.BLUE + status + colorama.Fore.RESET
            elif status == "broadcasted":
                status = colorama.Fore.YELLOW + status + colorama.Fore.RESET
            elif status == "success":
                status = colorama.Fore.GREEN + status + colorama.Fore.RESET
            elif status == "failed":
                status = colorama.Fore.RED + status + colorama.Fore.RESET
            else:
                raise RuntimeError("Does not compute")

            table.append((tx.txid, status, tx.nonce, tx.get_from(), tx.get_to(), tx.human_readable_description[0:64]))

        print(tabulate(table, headers=["TXID", "Status", "Nonce", "From", "To", "Note"]))












