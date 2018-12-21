import datetime

from sqlalchemy.orm import Session
from web3 import Web3

from sto.models.tokenscan import _TokenHolderLastBalance


class TokenScanner:
    """Scan blockchain for token transfer events and build a database of balances at certain timepoints (blocks)."""

    def __init__(self, network: str, dbsession: Session, web3: Web3, token_address: str, TokenScanStatus: type, TokenHolderStatus: type, TokenHolderLastBalance: type):

        assert isinstance(web3, Web3)

        self.network = network  # "kovan"
        self.dbsession = dbsession
        self.web3 = web3
        self.token_address = token_address

        # SQLAlchemy models, allow caller to supply their own
        self.TokenScanStatus = TokenScanStatus  #: type sto.models.implementation.TokenScanStatus
        self.TokenHolderStatus = TokenHolderStatus #: type sto.models.implementation.TokenHolderStatus
        self.TokenHolderLastBalance = TokenHolderLastBalance #: type sto.models.implementation.TokenHolderLastBalance

    @property
    def address(self):
        return self.token_address

    def get_or_create_status(self):
        assert self.address.startswith("0x")
        assert self.network in ("kovan", "ethereum", "testing", "ropsten")  # TODO: Sanity check - might want to remove this

        account = self.dbsession.query(self.TokenScanStatus).filter_by(network=self.network, address=self.address).one_or_none()
        if not account:
            account = self.TokenScanStatus(network=self.network, address=self.address)
            self.dbsession.add(account)
            self.dbsession.flush()
        return account

    def get_block_timestamp(self, block_num) -> datetime.datetime:
        """Get Ethereum block timestamp"""
        block_info = self.web3.eth.getBlock(block_num)
        last_time = block_info["timestamp"]
        return datetime.datetime.utcfromtimestamp(last_time)

    def drop_old_data(self, before_block: int):
        """Purge old data in the case of a rescan."""
        status = self.get_or_create_status()
        status.holder_deltas.filter_by(self.TokenHolderStatus.block_num < before_block).delete()

    def calculate_sum_from_deltas(self, token_holder: str):
        """Denormalize the token balance.

        Drop in a PostgreSQL implementation here using native databae types.
        """
        assert token_holder.startswith("0x")

    def get_or_create_last_balance(self, token_holder: str) -> _TokenHolderLastBalance:
        """Denormalize the token balance.

        Drop in a PostgreSQL implementation here using native databae types.
        """
        assert token_holder.startswith("0x")

        status = self.get_or_create_status()
        account = status.balances.filter_by(address=token_holder).one_or_none()
        if not account:
            account = self.TokenHolderLastBalance(address=token_holder)
            status.balances.append(account)
            self.dbsession.flush()

        return account

    def get_or_create_last_balance(self, token_holder: str) -> _TokenHolderLastBalance:
        """Denormalize the token balance.

        Drop in a PostgreSQL implementation here using native databae types.
        """
        assert token_holder.startswith("0x")

        status = self.get_or_create_status()
        account = status.balances.filter_by(address=token_holder).one_or_none()
        if not account:
            account = self.TokenHolderLastBalance(address=token_holder)
            status.balances.append(account)
            self.dbsession.flush()

        return account

    def scan_chunk(self, start_block, end_block):
        """Populate TokenHolderStatus for certain blocks.
        """


    def scan(self, start_block, end_block, chunk_size=20):
        """Perform a token balances scan.

        Assumes all balances in the database are valid before start_block (no forks sneaked in).

        :param start_block:
        :param end_block:
        :return:
        """
        self.drop_old_data(start_block)

        current_block = start_block
        updated_token_holders = set()  # Token holders that get updates

        # Scan in chunks, commit between
        while current_block <= end_block:
            current_end = current_block + chunk_size

            mutated_addresses = self.scan_chunk(current_block, current_end)
            updated_token_holders.add(mutated_addresses)

            self.dbsession.commit()  # Update database on the disk
            current_block = current_end

        # Update the final balances
        for mutated_address in mutated_addresses:
            balance_now, last_updated_block, last_block_updated_at = self.calculate_sum_from_deltas(mutated_addresses)
            last_balance = self.get_or_create_last_balance(mutated_address)
            last_balance.set_balance_uint(balance_now)
            last_balance.end_block = last_updated_block
            last_balance.end_block_timestamp = last_block_updated_at

        self.dbsession.commit()  # Write latest balances

