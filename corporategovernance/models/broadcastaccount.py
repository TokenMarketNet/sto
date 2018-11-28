import sqlalchemy as sa

from corporategovernance.models.utils import TimeStampedBaseModel


class _BroadcastAccount(TimeStampedBaseModel):
    """Account that we maintain for broadcast transactions."""

    __tablename__ = "broadcast_account"

    #: Network name like "kovan"
    network = sa.Column(sa.String(256), nullable=False, unique=False)

    #: Address of the account, like 0x000000
    address = sa.Column(sa.String(256), nullable=False, unique=False)

    #: Currently available nonce to be allocated for the next transaction
    current_nonce = sa.Column(sa.Integer, default=1)



class _PreparedTransaction(TimeStampedBaseModel):
    """Manage transactions.

    Make is safe to rebroadcast.
    """

    __tablename__ = "prepared_transaction"

    nonce = sa.Column(sa.Integer, default=1)

    #: Network name like "kovan"
    account = sa.Column(sa.String(256), nullable=False, unique=False)

    # Is this a contract deployment transaction
    contract_deployment = sa.Column(sa.Boolean, nullable=False, default=False)

    #: For diagnostics purpose
    human_readable_description = sa.Column(sa.Text, nullable=False, unique=False)

    #: Address of the upcoming deployed contract or token contract address interacted with
    contract_address = sa.Column(sa.String(256), nullable=True, unique=False)

    #: Address of the account, like 0x000000, for the user account that receives the transaction for tokens
    receiver = sa.Column(sa.String(256), nullable=False, unique=False)

    #: Raw payload of the transaction to be broadcasted
    unsigned_payload = sa.Column(sa.Text, nullable=False, unique=False)

    #: Precalculated transaction id
    txid = sa.Column(sa.String(256), nullable=True, unique=False)

    #: Value transferred in Ethereum transaction
    value = sa.Column(sa.Numeric(60, 20), nullable=False, default=0)

    #: How much gwei we paid for this in Ethereum network
    gas_price = sa.Column(sa.Numeric(60, 20), nullable=False, default=0)

    #: Wat was the gas limit in Etheruem network
    gas_limit = sa.Column(sa.Numeric(60, 20), nullable=False, default=0)

    #: When we attempted this transaction was broadcasted to the network
    broadcasted_at = sa.Column(sa.DateTime, default=None)

    #: When was the last attempt to rebroadcast this transaction
    rebroadcasted_at = sa.Column(sa.DateTime, default=None)

    #: When did we poll and received that the transaction was included in a block
    result_fetched_at = sa.Column(sa.DateTime, default=None)

    #: What was the resulting block where this transaction was included
    result_block_num = sa.Column(sa.Integer, default=None)

    #: Did the transaction success or fail
    result_transaction_success = sa.Column(sa.Boolean, default=None)

    #: Human readable failure reason
    result_transaction_reason = sa.Column(sa.String(256), default=None)


