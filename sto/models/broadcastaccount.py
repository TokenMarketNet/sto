from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from sto.models.utils import TimeStampedBaseModel, UTCDateTime


class _BroadcastAccount(TimeStampedBaseModel):
    """Account status we maintain for broadcast transactions."""

    __tablename__ = "broadcast_account"

    #: Network name like "kovan", "ethereum"
    network = sa.Column(sa.String(256), nullable=False)

    #: Address of the account as hex string, like 0x000000
    address = sa.Column(sa.String(256), nullable=False)

    #: Currently available nonce to be allocated for the next transaction
    current_nonce = sa.Column(sa.Integer, default=0)

    @classmethod
    def get_transactions_for_network(cls, dbsession: Session, network: str):
        account = dbsession.query(cls).filter_by(network=network).one()
        return account.txs



class _PreparedTransaction(TimeStampedBaseModel):
    """Manage transactions.

    Make is safe to rebroadcast.
    """

    __tablename__ = "prepared_transaction"

    #: Ethereum transaction nonce allocated from BroadcastAccount for this transaction
    nonce = sa.Column(sa.Integer, default=1)

    #: What is the corresponding transaction for this crypto transactions in other systems. Could be payment TXID or fiat receipt id in the case of purchasing shares. Under normal circumstances PreparedTransaction should not have duplicate external_ids but this may change under rebroadcast and other manual fix ups.
    external_id = sa.Column(sa.String(256), nullable=True)

    # Is this a contract deployment transaction
    contract_deployment = sa.Column(sa.Boolean, nullable=False, default=False)

    #: For diagnostics purpose
    human_readable_description = sa.Column(sa.Text, nullable=False)

    #: Address of the upcoming deployed contract or token contract address interacted with
    contract_address = sa.Column(sa.String(256), nullable=True)

    #: Address of the account, like 0x000000, for benefactor who receives the tokens. Not applicable for contract deployments.
    receiver = sa.Column(sa.String(256), nullable=True)

    #: Raw payload of the transaction to be broadcasted
    unsigned_payload = sa.Column(sa.JSON, nullable=False)

    #: Precalculated transaction id
    txid = sa.Column(sa.String(256), nullable=True)

    #: Value transferred in Ethereum transaction
    # value = sa.Column(sa.Numeric(60, 20), nullable=False, default=0)

    #: How much gwei we paid for this in Ethereum network
    # gas_price = sa.Column(sa.Numeric(60, 20), nullable=False, default=0)

    #: Wat was the gas limit in Etheruem network
    # gas_limit = sa.Column(sa.Numeric(60, 20), nullable=False, default=0)

    #: When we attempted this transaction was broadcasted to the network
    broadcasted_at = sa.Column(UTCDateTime, default=None)

    #: When was the last attempt to rebroadcast this transaction
    #: TODO: Not in use yet.
    rebroadcasted_at = sa.Column(UTCDateTime, default=None)

    #: When did we poll and received that the transaction was included in a block
    result_fetched_at = sa.Column(UTCDateTime, default=None)

    #: What was the resulting block where this transaction was included
    result_block_num = sa.Column(sa.Integer, default=None)

    #: Did the transaction success or fail
    result_transaction_success = sa.Column(sa.Boolean, default=None)

    #: Human readable failure reason
    result_transaction_reason = sa.Column(sa.String(256), default=None)

    #: When a contract deployment was verified at EtherScan
    verified_at = sa.Column(UTCDateTime, default=None)

    #: Misc. transaction data - like ABI with source code information for verification, verification info
    other_data = sa.Column(sa.JSON, nullable=False, default=dict)

    @property
    def gas_limit(self):
        return self.unsigned_payload["gas"]

    @property
    def gas_price(self):
        return self.unsigned_payload["gasPrice"]

    def get_status(self) -> str:
        """Machine/human readable status."""
        if not self.broadcasted_at:
            return "waiting"
        elif self.broadcasted_at and not self.result_fetched_at:
            return "broadcasted"
        elif self.result_fetched_at:

            if self.verified_at:
                return "verified"
            elif self.result_block_num:
                if self.result_transaction_success:
                    return "success"
                else:
                    return "failed"
            else:
                return "mining"
        else:
            raise RuntimeError("State error")

    def get_to(self) -> str:
        return self.receiver or self.contract_address

    def get_from(self) -> str:
        return self.broadcast_account.address

    @property
    def abi(self) -> Optional["str"]:
        """Source code used for a deployment transaction for contract verification."""
        return self.other_data["abi"]["source"]

    @abi.setter
    def abi(self, val):
        self.other_data["abi"] = val
        flag_modified(self, "other_data")

    @property
    def verification_info(self) -> Optional["str"]:
        """EtherScan reply for contract verification."""
        return self.other_data["verification_info"]

    @verification_info.setter
    def verification_info(self, val):
        assert type(val) == dict
        self.other_data["verification_info"] = val
        flag_modified(self, "other_data")

    @property
    def flattened_source_code(self) -> Optional["str"]:
        """Source code used for a deployment transaction for contract verification."""
        return self.other_data["abi"]["source"]

    @property
    def compiler_version(self) -> Optional["str"]:
        """Compiled version used for verification."""
        return self.other_data["abi"]["metadata"]["compiler"]["version"]

    @property
    def contract_name(self) -> Optional["str"]:
        """Compiled version used for verification."""
        abi = self.other_data["abi"]
        return abi["name"]

    @property
    def constructor_arguments(self) -> Optional[str]:
        """The contract payload used for the constructor.

        Needed for source code verification.
        """
        return self.other_data["constructor_arguments"]

    @constructor_arguments.setter
    def constructor_arguments(self, val):
        assert val.startswith("0x")
        self.other_data["constructor_arguments"] = val
        flag_modified(self, "other_data")

    def is_token_contract_deployment(self) -> bool:
        """Is this transaction to deploy a token contract.

        To separate for deploying transfer agents, etc. other smart contracts.
        """
        return self.contract_name in ("SecurityToken",)

    @classmethod
    def filter_by_contract_name(cls, contract_name):
        return sa.cast(
            cls.other_data['abi']['name'], sa.String
        ) == '"{0}"'.format(contract_name)

