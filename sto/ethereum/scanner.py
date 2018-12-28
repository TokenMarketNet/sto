import datetime
import time
from logging import Logger

from eth_utils import to_checksum_address
from sqlalchemy.orm import Session
from typing import Set, Dict, Tuple
from web3 import Web3
from web3.contract import Contract

from sto.ethereum.utils import getLogs
from sto.models.tokenscan import _TokenHolderLastBalance, _TokenScanStatus


class TokenScanner:
    """Scan blockchain for token transfer events and build a database of balances at certain timepoints (blocks)."""

    #: How far back in the past we jump to detect works in incremental rescans
    NUM_BLOCKS_RESCAN_FOR_FORKS = 10

    def __init__(self, logger: Logger, network: str, dbsession: Session, web3: Web3, abi: dict, token_address: str, TokenScanStatus: type, TokenHolderDelta: type, TokenHolderLastBalance: type):

        assert isinstance(web3, Web3)

        self.logger = logger
        self.network = network  # "kovan"
        self.dbsession = dbsession
        self.web3 = web3
        self.token_address = token_address
        self.abi = abi   # We need to know ERC20Standard

        # SQLAlchemy models, allow caller to supply their own
        self.TokenScanStatus = TokenScanStatus  #: type sto.models.implementation.TokenScanStatus
        self.TokenHolderDelta = TokenHolderDelta #: type sto.models.implementation.TokenHolderDelta
        self.TokenHolderLastBalance = TokenHolderLastBalance #: type sto.models.implementation.TokenHolderLastBalance]

        # What is the minimim
        self.min_scan_chunk_size = 10 # 12 s/block = 120 seconds period
        self.max_scan_chunk_size = 500000

        # Factor how fast we increase the chunk size if results are found
        # # (slow down scan after starting to get hits)
        self.chunk_size_decrease = 0.5

        # Factor how was we increase chunk size if no results found
        self.chunk_size_increase = 20.0

    @property
    def address(self):
        return self.token_address

    def get_or_create_status(self) -> _TokenScanStatus:
        assert self.address.startswith("0x")
        assert self.network in ("kovan", "ethereum", "testing", "ropsten")  # TODO: Sanity check - might want to remove this

        account = self.dbsession.query(self.TokenScanStatus).filter_by(network=self.network, address=self.address).one_or_none()
        if not account:
            account = self.TokenScanStatus(network=self.network, address=self.address)
            account.decimals = self.get_token_contract_decimals(self.address)
            self.dbsession.add(account)
            self.dbsession.flush()
        return account

    def get_contract_proxy(self, contract_name: str, address: str) -> Contract:
        """Get web3.Contract to interact directly with the network"""
        abi_data = self.abi[contract_name]

        contract_class = Contract.factory(
            web3=self.web3,
            abi=abi_data["abi"],
            bytecode=abi_data["bytecode"],
            bytecode_runtime=abi_data["bytecode_runtime"],
            )

        return contract_class(address=to_checksum_address(address))

    def get_token_contract(self, address) -> Contract:
        return self.get_contract_proxy("SecurityToken", address)

    def get_token_contract_decimals(self, token_address) -> int:
        """Ask token contract decimal amount using web3 and ABI."""
        contract = self.get_token_contract(token_address)
        return contract.functions.decimals().call()

    def get_block_timestamp(self, block_num) -> datetime.datetime:
        """Get Ethereum block timestamp"""
        block_info = self.web3.eth.getBlock(block_num)
        last_time = block_info["timestamp"]
        return datetime.datetime.utcfromtimestamp(last_time)

    def get_suggested_scan_start_block(self):
        """Get where we should start to scan for new token events.

        If there are no prior scans start from block 1.
        Otherwise start from the last end block minus ten blocks.
        We rescan the last ten scanned blocks in the case there were forks to avoid
        misaccounting due to minor single block works (happens once in a hour in Ethereum).
        These heurestics could be made more robust, but this is for the sake of simple reference implementation.
        """
        status = self.get_or_create_status()
        if status.end_block:
            return max(1, status.end_block - TokenScanner.NUM_BLOCKS_RESCAN_FOR_FORKS)
        return 1

    def get_suggested_scan_end_block(self):
        """Get the last mined block."""
        return self.web3.eth.blockNumber

    def drop_old_data(self, after_block: int):
        """Purge old data in the case of a rescan."""
        status = self.get_or_create_status()
        status.holder_deltas.filter(self.TokenHolderDelta.block_num >= after_block).delete()

    def calculate_sum_from_deltas(self, token_holder: str) -> Tuple[int, int, datetime.datetime]:
        """Denormalize the token balance.

        Drop in a more efficient PostgreSQL implementation here using native database types.
        """
        assert token_holder.startswith("0x")

        sum = last_block_num = 0
        last_updated_at = None

        status = self.get_or_create_status()
        deltas = status.holder_deltas.filter_by(address=token_holder).order_by(self.TokenHolderDelta.block_num, self.TokenHolderDelta.tx_internal_order)
        for d in deltas:
            sum += d.get_delta_uint()
            last_block_num = d.block_num
            last_updated_at = d.block_timestamped_at
        return sum, last_block_num, last_updated_at

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

        return account

    def create_deltas(self, block_num: int, block_when: datetime, txid: str, idx: int, from_: str, to_: str, value: int):
        """Creates token balance change events in the database.

        For each token transfer we create debit and credit events, so that we can nicely sum the total balance of the account.
        """
        status = self.get_or_create_status()

        assert txid.startswith("0x")
        assert from_.startswith("0x")
        assert to_.startswith("0x")

        existing = status.holder_deltas.filter_by(block_num=block_num, tx_internal_order=idx).first()
        if existing:
            raise RuntimeError("Had already existing imported event: {}".format(existing))

        delta_credit = self.TokenHolderDelta(address=to_, block_num=block_num, txid=txid, tx_internal_order=idx, block_timestamped_at=block_when)
        delta_credit.set_delta_uint(value, +1)
        status.holder_deltas.append(delta_credit)

        if from_ != self.TokenHolderDelta.NULL_ADDRESS:
            delta_debit = self.TokenHolderDelta(address=from_, block_num=block_num, txid=txid, tx_internal_order=idx, block_timestamped_at=block_when)
            delta_debit.set_delta_uint(value, -1)
            status.holder_deltas.append(delta_debit)

    def scan_chunk(self, start_block, end_block) -> Set[str]:
        """Populate TokenHolderStatus for certain blocks.

        :return: Set of addresses where balance changes between scans.
        """

        mutated_addresses = set()
        token = self.get_token_contract(self.address)

        # Discriminate between ERC-20 transfer and ERC-667
        # The latter is not used anywhere yet AFAIK
        Transfer = token.events.Transfer("from", "to", "value")
        Issued = token.events.Issued("to", "value")
        block_timestamps = {}
        get_block_timestamp = self.get_block_timestamp

        # Cache block timestamps to reduce some RPC overhead
        # Real solution would be smarter models around block
        def get_block_when(block_num):
            if not block_num in block_timestamps:
                block_timestamps[block_num] = get_block_timestamp(block_num)
            return block_timestamps[block_num]

        for event_type in [Issued, Transfer]:

            # events = event_type.createFilter(fromBlock=start_block, toBlock=end_block).get_all_entries()

            events = getLogs(event_type, fromBlock=start_block, toBlock=end_block)

            # AttributeDict({'args': AttributeDict({'from': '0xDE5bC059aA433D72F25846bdFfe96434b406FA85', 'to': '0x0bdcc26C4B8077374ba9DB82164B77d6885b92a6', 'value': 300000000000000000000}), 'event': 'Transfer', 'logIndex': 0, 'transactionIndex': 0, 'transactionHash': HexBytes('0x973eb270e311c23dd6173a9092c9ad4ee8f3fe24627b43c7ad75dc2dadfcbdf9'), 'address': '0x890042E3d93aC10A426c7ac9e96ED6416B0cC616', 'blockHash': HexBytes('0x779f55173414a7c0df0d9fc0ab3fec461a66ceeee0b4058e495d98830c92abf8'), 'blockNumber': 7})
            for e in events:
                idx = e["logIndex"]  # nteger of the log index position in the block. null when its pending log.
                if idx is None:
                    raise RuntimeError("Somehow tried to scan a pending block")

                if e["event"] == "Issued":
                    # New issuances pop up from empty air - mark this specially in the database.
                    # Also some ERC-20 tokens use Transfer from null address to symbolise issuance.
                    from_ = self.TokenHolderDelta.NULL_ADDRESS
                else:
                    from_ = e["args"]["from"]
                    mutated_addresses.add(e["args"]["from"])

                block_when = get_block_when(e["blockNumber"])

                self.create_deltas(e["blockNumber"], block_when, e["transactionHash"].hex(), idx, from_, e["args"]["to"], e["args"]["value"])
                self.logger.debug("Imported %s, token:%s block:%d from:%s to:%s value:%s", e["event"], self.address, e["blockNumber"], from_, e["args"]["to"], e["args"]["value"])

                mutated_addresses.add(e["args"]["to"])

        return mutated_addresses

    def update_denormalised_balances(self, mutated_addresses: set) -> dict:
        """Update the quick read table for the current balance of a token holder."""
        result = {}

        self.logger.debug("Recalculating final token balances on token %s for %d addresses", self.address, len(mutated_addresses))
        for mutated_address in mutated_addresses:
            balance_now, last_updated_block, last_block_updated_at = self.calculate_sum_from_deltas(mutated_address)
            last_balance = self.get_or_create_last_balance(mutated_address)
            last_balance.set_balance_uint(balance_now)
            last_balance.last_updated_block = last_updated_block
            last_balance.last_block_updated_at = last_block_updated_at

            result[mutated_address] = balance_now

        return result

    def estimate_next_chunk_size(self, current_chuck_size: int, event_found_count: int):
        """Try to figure out optimal chunk size

        Our scanner might need to scan the whole blockchain for all events

        * We want to minimize API calls over empty blocks

        * We want to make sure that one scan chunk does not try to process too many entries once, as we try to control commit buffer size and potentially asynchronous busy loop

        * Do not overload node serving JSON-RPC API

        This heurestics exponentiallt increases and decreases the scan chunk size depending on if we are seeing events or not.
        It does not make sense to do a full chain scan starting from block 1, doing one JSON-RPC call per 20 blocks.
        """

        if event_found_count > 0:
            current_chuck_size *= self.chunk_size_increase
        else:
            current_chuck_size *= self.chunk_size_decrease

        current_chuck_size = max(self.min_scan_chunk_size, current_chuck_size)
        current_chuck_size = min(self.max_scan_chunk_size, current_chuck_size)
        return current_chuck_size

    def scan(self, start_block, end_block, start_chunk_size=20) -> dict:
        """Perform a token balances scan.

        Assumes all balances in the database are valid before start_block (no forks sneaked in).

        :param start_block: The first block included in the scan

        :param end_block: The last block included in the scan

        :return: Address -> last balance mapping for all address balances that changed during those blocks
        """

        assert start_block <= end_block

        self.drop_old_data(start_block)

        current_block = start_block
        updated_token_holders = set()  # Token holders that get updates

        # Scan in chunks, commit between
        chunk_size = start_chunk_size
        mutated_addresses = set()
        last_scan_duration = 0
        while current_block <= end_block:

            current_end = min(current_block + chunk_size, end_block)

            # Print some diagnostics to logs to try to fiddle with real world JSON-RPC API performance
            self.logger.debug("Scanning token transfers for blocks: %d - %d, chunk size %d, last chunk scan took %f", current_block, current_end, chunk_size, last_scan_duration)
            start = time.time()
            mutated_addresses = self.scan_chunk(current_block, current_end)
            last_scan_duration = time.time() - start

            updated_token_holders.update(mutated_addresses)

            self.dbsession.commit()  # Update database on the disk
            current_block = current_end + 1

            chunk_size = self.estimate_next_chunk_size(chunk_size, len(mutated_addresses))

        result = self.update_denormalised_balances(mutated_addresses)

        # Update token scan status
        status = self.get_or_create_status()
        if not status.start_block:
            status.start_block = start_block

        status.end_block = end_block

        self.dbsession.commit()  # Write latest balances

        return result

