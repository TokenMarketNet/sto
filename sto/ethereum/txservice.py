from logging import Logger

import requests
import time
from eth_account.internal.transactions import assert_valid_fields
from sto.ethereum.utils import mk_contract_address, get_constructor_arguments
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



class AddressConfigurationMismatch(Exception):
    pass


class CouldNotVerifyOnEtherScan(Exception):
    pass


class EthereumStoredTXService:
    """A transaction service that writes entries to a local database before trying to broadcast them to the blockchain."""

    #: Can't trust auto estimate
    SPECIAL_GAS_LIMIT_FOR_CONTRACT_DEPLOYMENT = 3500000  # Number from Ethereum tester, cannot exceed this

    #: Can't trust auto estimate
    SPECIAL_GAS_LIMIT_FOR_NORMAL_TX = 666111

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


        if gas_limit:
            assert type(gas_limit) == int

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
        assert self.network in ("kovan", "ethereum", "testing", "ropsten")  # TODO: Sanity check - might want to remove this

        account = self.dbsession.query(self.broadcast_account_model).filter_by(network=self.network, address=self.address).one_or_none()
        if not account:
            account = self.broadcast_account_model(network=self.network, address=self.address)
            self.dbsession.add(account)
            self.dbsession.flush()

        return account

    def get_next_nonce(self):
        broadcast_account = self.get_or_create_broadcast_account()
        return broadcast_account.current_nonce

    def ensure_accounts_in_sync(self):
        """Make sure that our internal nonce and external nonce looks correct."""

        broadcast_account = self.get_or_create_broadcast_account()

        tx_count = self.web3.eth.getTransactionCount(broadcast_account.address)

        if tx_count != broadcast_account.current_nonce:
            NetworkAndDatabaseNonceOutOfSync("Nonced out of sync. Network: {}, database: {}. Maybe you have a pending broadcasts propagating?".format(tx_count, broadcast_account.current_nonce))

    def allocate_transaction(self,
                             broadcast_account: _BroadcastAccount,
                             receiver: Optional[str],
                             contract_address: Optional[str],
                             contract_deployment: bool,
                             nonce: int,
                             note: str,
                             unsigned_payload: dict,
                             gas_price: Optional[int],
                             gas_limit: Optional[int],
                             external_id: Optional[str]=None,
                             ) -> _PreparedTransaction:
        """Put a transaction to the pending queue of the current broadcast list."""

        if receiver:
            assert receiver.startswith("0x")

        assert contract_deployment in (True, False)

        assert broadcast_account.current_nonce == nonce

        assert type(unsigned_payload) == dict

        assert_valid_fields(unsigned_payload)

        tx = self.prepared_tx_model()  # type: _PreparedTransaction
        tx.nonce = nonce
        tx.human_readable_description = note
        tx.receiver = receiver
        tx.contract_address = contract_address
        tx.contract_deployment = contract_deployment
        tx.unsigned_payload = unsigned_payload
        tx.external_id = external_id
        broadcast_account.txs.append(tx)
        broadcast_account.current_nonce += 1
        return tx

    def generate_tx_data(self, nonce: int, contract_tx=False) -> dict:
        """Generate transaction control parameters.

        :param contract: We use a special hardcoded gas estimate for 4,000,000 when deploying contracts. Kovan misestimates the cost of deploying SecurityToken and thus the transaction always fails with the auto estimate.
        """

        # See TRANSACTION_VALID_VALUES
        tx_data = {}
        tx_data["nonce"] = nonce


        # Mikko's rule of thumb estimator because local accounts do not estimate gas too well
        if self.gas_limit:
            tx_data["gas"] = self.gas_limit
        elif contract_tx:
            tx_data["gas"] = EthereumStoredTXService.SPECIAL_GAS_LIMIT_FOR_CONTRACT_DEPLOYMENT
        else:
            tx_data["gas"] = EthereumStoredTXService.SPECIAL_GAS_LIMIT_FOR_NORMAL_TX

        if self.gas_price:
            tx_data["gasPrice"] = self.gas_price

        return tx_data

    def deploy_contract(self, contract_name: str, abi: dict, note: str, constructor_args=None) -> _PreparedTransaction:
        """Deploys a contract."""

        if not constructor_args:
            constructor_args = {}

        abi_data = abi[contract_name]

        assert "source" in abi_data, "We need to have special postprocessed ABI data bundle, as we need the contract source code for EtherScan verification"

        contract_class = Contract.factory(
            web3=self.web3,
            abi=abi_data["abi"],
            bytecode=abi_data["bytecode"],
            bytecode_runtime=abi_data["bytecode_runtime"],
            )

        broadcast_account = self.get_or_create_broadcast_account()

        next_nonce = self.get_next_nonce()

        # Creates a dict for signing
        tx_data = self.generate_tx_data(next_nonce, contract_tx=True)
        constructed_txn = contract_class.constructor(**constructor_args).buildTransaction(tx_data)

        constructor_arguments = get_constructor_arguments(contract_class, kwargs=constructor_args)

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

        self.dbsession.flush()  # Populate other_data

        tx.abi = abi_data
        tx.constructor_arguments = constructor_arguments
        assert tx.compiler_version
        assert tx.flattened_source_code

        return tx

    def get_contract_proxy(self, contract_name: str, abi: dict, address: str, use_bytecode: bool=True) -> Contract:
        """Get web3.Contract to interact directly with the network"""
        abi_data = abi[contract_name]

        contract_class = Contract.factory(
            web3=self.web3,
            abi=abi_data["abi"],
        )
        if use_bytecode:
            contract_class.bytecode = abi_data["bytecode"],
            contract_class.bytecode_runtime = abi_data["bytecode_runtime"],

        return contract_class(address=to_checksum_address(address))

    def interact_with_contract(self, contract_name: str, abi: dict, address: str, note: str, func_name: str, args=None, receiver=None, use_bytecode=True) -> _PreparedTransaction:
        """Does a transaction against a contract."""

        assert address.startswith("0x")

        if not args:
            args = {}

        contract = self.get_contract_proxy(contract_name, abi, address, use_bytecode=use_bytecode)
        broadcast_account = self.get_or_create_broadcast_account()

        next_nonce = self.get_next_nonce()

        func = contract.get_function_by_name(func_name)
        tx_data = self.generate_tx_data(next_nonce)
        constructed_txn = func(**args).buildTransaction(tx_data)

        tx = self.allocate_transaction(
            broadcast_account=broadcast_account,
            receiver=receiver,
            contract_address=address,
            contract_deployment=False,
            nonce=next_nonce,
            note=note,
            unsigned_payload=constructed_txn,
            gas_price=self.gas_price,
            gas_limit=self.gas_limit,
        )
        self.dbsession.flush()
        return tx

    def is_distributed(self, external_id: str, contract_address: str) -> bool:
        """Prevent us sending the same transaction twice."""
        if self.dbsession.query(self.prepared_tx_model).filter_by(external_id=external_id, contract_address=contract_address).one_or_none():
            return True
        return False

    def distribute_tokens(self, external_id: str, receiver_address: str, raw_amount: int, token_address: str, abi: dict, note: str, contract_name="ERC20", func_name="transfer", receiver=None) -> _PreparedTransaction:
        """Send out tokens."""

        assert receiver_address.startswith("0x")
        assert token_address.startswith("0x")
        assert type(raw_amount) == int
        assert raw_amount >= 1

        # Prevent us sending the same transaction twice
        if self.dbsession.query(self.prepared_tx_model).filter_by(external_id=external_id, contract_address=token_address).one_or_none():
            raise RuntimeError("Already distributed token:{} id:{}".format(token_address, external_id))

        contract = self.get_contract_proxy(contract_name, abi, token_address)
        broadcast_account = self.get_or_create_broadcast_account()

        next_nonce = self.get_next_nonce()

        args = [receiver_address, raw_amount]
        func = getattr(contract.functions, func_name)

        tx_data = self.generate_tx_data(next_nonce)
        constructed_txn = func(*args).buildTransaction(tx_data)

        tx = self.allocate_transaction(
            broadcast_account=broadcast_account,
            receiver=receiver_address,
            contract_address=token_address,
            contract_deployment=False,
            nonce=next_nonce,
            note=note,
            unsigned_payload=constructed_txn,
            gas_price=self.gas_price,
            gas_limit=self.gas_limit,
            external_id=external_id,
        )
        self.dbsession.flush()
        return tx

    def get_raw_token_balance(self, token_address: str, abi: dict, contract_name="ERC20Basic", func_name="balanceOf") -> int:
        """Check that we have enough token balance for distribute operations."""

        assert token_address.startswith("0x")

        contract = self.get_contract_proxy(contract_name, abi, token_address)
        broadcast_account = self.get_or_create_broadcast_account()

        args = {
            "who": broadcast_account.address,
        }
        func = getattr(contract.functions, func_name)

        result = func(**args).call()
        return result

    def get_pending_broadcasts(self) -> Query:
        """All transactions that need to be broadcasted."""
        return self.dbsession.query(self.prepared_tx_model).filter_by(broadcasted_at=None).order_by(self.prepared_tx_model.nonce).join(self.broadcast_account_model).filter_by(network=self.network)

    def get_unmined_txs(self) -> Query:
        """All transactions that do not yet have a block assigned."""
        return self.dbsession.query(self.prepared_tx_model).filter(self.prepared_tx_model.txid != None).filter_by(result_block_num=None).join(self.broadcast_account_model).filter_by(network=self.network)

    def get_last_transactions(self, limit: int) -> Query:
        """Fetch latest transactions."""
        assert type(limit) == int
        return self.dbsession.query(self.prepared_tx_model).order_by(self.prepared_tx_model.created_at.desc()).limit(limit)

    def broadcast(self, tx: _PreparedTransaction):
        """Push transactions to Ethereum network."""

        if tx.broadcast_account.address != self.address:
            raise AddressConfigurationMismatch("Could not broadcast due to address mismatch. A pendign transaction was created for account {}, but we are using configured account {}".format(tx.broadcast_account.addres, self.address))

        tx_data = tx.unsigned_payload
        signed = self.web3.eth.account.signTransaction(tx_data, self.private_key_hex)
        tx.txid = signed.hash.hex()
        self.web3.eth.sendRawTransaction(signed.rawTransaction)
        tx.broadcasted_at = now()
        return tx

    def update_status(self, tx: _PreparedTransaction):
        """Update tx status from Etheruem network."""

        assert tx.txid

        # https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.getTransactionReceipt
        receipt = self.web3.eth.getTransactionReceipt(tx.txid)
        if receipt:
            tx.result_block_num = receipt["blockNumber"]

            # https://ethereum.stackexchange.com/a/6003/620
            if receipt["status"] == 0:
                tx.result_transaction_success = False
                tx.result_transaction_reason = "Transaction failed"  # TODO: Need some logic to separate failure modes
            else:
                tx.result_transaction_success = True

        tx.result_fetched_at = now()
        return tx

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
            elif status == "mining":
                status = colorama.Fore.YELLOW + status + colorama.Fore.RESET
            elif status in ("success", "verified"):
                status = colorama.Fore.GREEN + status + colorama.Fore.RESET
                status += ":" + str(tx.result_block_num)
            elif status == "failed":
                status = colorama.Fore.RED + status + colorama.Fore.RESET
                status += ":" + str(tx.result_block_num)
            else:
                raise RuntimeError("Does not compute")

            table.append((tx.txid, status, tx.nonce, tx.get_from(), tx.get_to(), tx.human_readable_description[0:64]))

        print(tabulate(table, headers=["TXID", "Status and block", "Nonce", "From", "To", "Note"]))


def verify_on_etherscan(logger: Logger, network: str, tx: _PreparedTransaction, api_key: str, session, timeout=120):
    """Verify a contrcact deployment on Etherscan.

    Uses https://etherscan.io/apis#contracts
    """

    assert network in ("ethereum", "kovan", "ropsten", "rinkerby")
    if network != "ethereum":
        url = "https://api-{}.etherscan.io/api".format(network)
    else:
        url = "https://api.etherscan.io/api"

    assert tx.result_transaction_success
    assert tx.contract_deployment

    source = tx.flattened_source_code

    assert source.strip(), "Source code missing"

    compiler = tx.compiler_version
    address = tx.contract_address
    constructor_arguments = tx.constructor_arguments
    contract_name = tx.contract_name

    data = {
        "apikey": api_key,
        "module": "contract",
        "contractaddress": address,
        "action": "verifysourcecode",
        "sourceCode": source,
        "contractname": contract_name,
        "compilerversion": "v" + compiler,  # https://etherscan.io/solcversions
        "constructorArguements": constructor_arguments[2:],  # Remove leading 0x
        "optimizationUsed": 1,  # TODO: Hardcoded
        "runs": 500, # TODO: Hardcoded
    }

    info_data = data.copy()
    del info_data["sourceCode"]  # Too verbose
    del info_data["apikey"]  # Security
    logger.info("Calling EtherScan API as: %s", info_data)

    #
    # Step 1: EtherScan validates input and gives us a ticket id to track the submission status
    #

    resp = session.post(url, data)
    # {'status': '0', 'message': 'NOTOK', 'result': 'Error!'}
    data = resp.json()

    logger.info("Etherscan replied %s", data)
    if data["status"] == "0":

        if "already verified" in data["result"]:
            return

        raise CouldNotVerifyOnEtherScan("Could not verify contract: " + address + " " + str(data))


    ticket = data["result"]

    #
    # Step 2: Poll for results
    #
    ready = False
    started = time.time()
    while not ready and time.time() < started + timeout:
        data = {
            "apikey": api_key,
            "module": "contract",
            "action": "checkverifystatus",
            "guid": ticket,
        }
        logger.info("Checking verification status on EtherScan API as: %s", info_data)
        resp = session.post(url, data)
        # {'status': '0', 'message': 'NOTOK', 'result': 'Error!'}
        data = resp.json()
        logger.info("Got reply %s", data)

        if data["result"] == "Pending in queue":
            # Keep polling
            #  {'status': '0', 'message': 'NOTOK', 'result': 'Pending in queue'}
            time.sleep(5)
            continue
        elif data["status"] == "0":
            # Produced binary did not match
            raise CouldNotVerifyOnEtherScan("Could not verify contract: " + address + " " + str(data))
        else:
            # All good
            assert data["status"] == "1"  # {'status': '1', 'message': 'OK', 'result': 'Pass - Verified'}
            break

    # Write to the database that we managed verify the contract
    tx.verified_at = now()
    tx.verification_info = data

    # //Submit Source Code for Verification
    # $.ajax({
    #     type: "POST",                       //Only POST supported
    #     url: "//api-kovan.etherscan.io/api", //Set to the  correct API url for Other Networks
    #     data: {
    #         apikey: $('#apikey').val(),                     //A valid API-Key is required
    #         module: 'contract',                             //Do not change
    #         action: 'verifysourcecode',                     //Do not change
    #         contractaddress: $('#contractaddress').val(),   //Contract Address starts with 0x...
    #         sourceCode: $('#sourceCode').val(),             //Contract Source Code (Flattened if necessary)
    #         contractname: $('#contractname').val(),         //ContractName
    #         compilerversion: $('#compilerversion').val(),   // see http://etherscan.io/solcversions for list of support versions
    #         optimizationUsed: $('#optimizationUsed').val(), //0 = Optimization used, 1 = No Optimization
    #         runs: 200,                                      //set to 200 as default unless otherwise
    #         constructorArguements: $('#constructorArguements').val(),   //if applicable
    #         libraryname1: $('#libraryname1').val(),         //if applicable, a matching pair with libraryaddress1 required
    #         libraryaddress1: $('#libraryaddress1').val(),   //if applicable, a matching pair with libraryname1 required
    #         libraryname2: $('#libraryname2').val(),         //if applicable, matching pair required
    #         libraryaddress2: $('#libraryaddress2').val(),   //if applicable, matching pair required
    #         libraryname3: $('#libraryname3').val(),         //if applicable, matching pair required
    #         libraryaddress3: $('#libraryaddress3').val(),   //if applicable, matching pair required
    #         libraryname4: $('#libraryname4').val(),         //if applicable, matching pair required
    #         libraryaddress4: $('#libraryaddress4').val(),   //if applicable, matching pair required
    #         libraryname5: $('#libraryname5').val(),         //if applicable, matching pair required
    #         libraryaddress5: $('#libraryaddress5').val(),   //if applicable, matching pair required
    #         libraryname6: $('#libraryname6').val(),         //if applicable, matching pair required
    #         libraryaddress6: $('#libraryaddress6').val(),   //if applicable, matching pair required
    #         libraryname7: $('#libraryname7').val(),         //if applicable, matching pair required
    #         libraryaddress7: $('#libraryaddress7').val(),   //if applicable, matching pair required
    #         libraryname8: $('#libraryname8').val(),         //if applicable, matching pair required
    #         libraryaddress8: $('#libraryaddress8').val(),   //if applicable, matching pair required
    #         libraryname9: $('#libraryname9').val(),         //if applicable, matching pair required
    #         libraryaddress9: $('#libraryaddress9').val(),   //if applicable, matching pair required
    #         libraryname10: $('#libraryname10').val(),       //if applicable, matching pair required
    #         libraryaddress10: $('#libraryaddress10').val()  //if applicable, matching pair required
    #     },
    #     success: function (result) {
    #         console.log(result);
    #         if (result.status == "1") {
    #             //1 = submission success, use the guid returned (result.result) to check the status of your submission.
    #             // Average time of processing is 30-60 seconds
    #             document.getElementById("postresult").innerHTML = result.status + ";" + result.message + ";" + result.result;
    #             // result.result is the GUID receipt for the submission, you can use this guid for checking the verification status
    #         } else {
    #             //0 = error
    #             document.getElementById("postresult").innerHTML = result.status + ";" + result.message + ";" + result.result;
    #         }
    #         console.log("status : " + result.status);
    #         console.log("result : " + result.result);
    #     },
    #     error: function (result) {
    #         console.log("error!");
    #         document.getElementById("postresult").innerHTML = "Unexpected Error"
    #     }
    # });

