import datetime
import time
from logging import Logger

from decimal import Decimal
from eth_utils import to_checksum_address
from sqlalchemy.orm import Session
from typing import Set, Dict, Tuple, Optional, Callable
from web3 import Web3
from web3.contract import Contract

from sto.ethereum.utils import getLogs
from sto.models.tokenscan import _TokenHolderAccount, _TokenScanStatus


class TokenScanner:
    """Scan blockchain for token transfer events and build a database of balances at certain timepoints (blocks)."""

    #: How far back in the past we jump to detect works in incremental rescans
    NUM_BLOCKS_RESCAN_FOR_FORKS = 10

    def __init__(self, logger: Logger, network: str, dbsession: Session, web3: Web3, abi: dict, token_address: str, TokenScanStatus: type, TokenHolderDelta: type, TokenHolderAccount: type):

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
        self.TokenHolderAccount = TokenHolderAccount #: type sto.models.implementation.TokenHolderAccount]

        # What is the minimim
        self.min_scan_chunk_size = 10 # 12 s/block = 120 seconds period

        # This should not exceed the reply size where Infura timeouts when it tries to dump
        # Tranfer events over this many blocks
        if network == "kovan":
            # Hack to speed up test token scans
            self.max_scan_chunk_size = 500000
        else:
            self.max_scan_chunk_size = 10000

        # Factor how fast we increase the chunk size if results are found
        # # (slow down scan after starting to get hits)
        self.chunk_size_decrease = 0.5

        # Factor how was we increase chunk size if no results found
        self.chunk_size_increase = 5.0

    @property
    def address(self):
        return self.token_address

    def get_or_create_status(self) -> _TokenScanStatus:
        assert self.address.startswith("0x")
        assert self.network in ("kovan", "ethereum", "testing", "ropsten")  # TODO: Sanity check - might want to remove this

        account = self.dbsession.query(self.TokenScanStatus).filter_by(network=self.network, address=self.address).one_or_none()
        if not account:
            account = self.TokenScanStatus(network=self.network, address=self.address)
            self.dbsession.add(account)
            self.dbsession.flush()

        return account

    def update_token_info(self):
        """Update token data."""
        name, symbol, decimals, token_supply = self.get_token_contract_info(self.address)
        status = self.get_or_create_status()
        status.name = name
        status.symbol = symbol
        status.decimals = decimals
        status.total_supply = str(Decimal(token_supply) / Decimal(10 ** decimals))

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

    def get_token_contract_info(self, token_address) -> [str, str, int, int]:
        """Ask token contract decimal amount using web3 and ABI."""
        contract = self.get_token_contract(token_address)
        return [contract.functions.name().call(), contract.functions.symbol().call(), contract.functions.decimals().call(), contract.functions.totalSupply().call()]

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

    def get_last_scanned_block(self):
        status = self.get_or_create_status()
        return status.end_block

    def delete_potentially_forked_block_data(self, after_block: int):
        """Purge old data in the case of a rescan."""
        status = self.get_or_create_status()
        self.TokenHolderDelta.delete_potentially_forked_block_data(status, after_block)

    def get_or_create_account(self, token_holder: str) -> _TokenHolderAccount:
        """Denormalize the token balance.

        Drop in a PostgreSQL implementation here using native databae types.
        """
        assert token_holder.startswith("0x")
        status = self.get_or_create_status()
        return status.get_or_create_account(token_holder)

    def create_deltas(self, block_num: int, block_when: datetime, txid: str, idx: int, from_: str, to_: str, value: int):
        """Creates token balance change events in the database.

        For each token transfer we create debit and credit events, so that we can nicely sum the total balance of the account.
        """
        status = self.get_or_create_status()
        status.create_deltas(block_num, block_when, txid, idx, from_, to_, value, self.TokenHolderDelta)
        self.dbsession.flush()

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
                    from_ = self.TokenScanStatus.NULL_ADDRESS
                else:
                    from_ = e["args"]["from"]
                    mutated_addresses.add(e["args"]["from"])

                block_when = get_block_when(e["blockNumber"])

                self.create_deltas(e["blockNumber"], block_when, e["transactionHash"].hex(), idx, from_, e["args"]["to"], e["args"]["value"])
                self.logger.debug("Imported %s, token:%s block:%d from:%s to:%s value:%s", e["event"], self.address, e["blockNumber"], from_, e["args"]["to"], e["args"]["value"])

                mutated_addresses.add(e["args"]["to"])

        return mutated_addresses

    def estimate_next_chunk_size(self, current_chuck_size: int, event_found_count: int):
        """Try to figure out optimal chunk size

        Our scanner might need to scan the whole blockchain for all events

        * We want to minimize API calls over empty blocks

        * We want to make sure that one scan chunk does not try to process too many entries once, as we try to control commit buffer size and potentially asynchronous busy loop

        * Do not overload node serving JSON-RPC API

        TODO: eth_getLogs does not provide meaningful way to get the block number when events start. Make a feature request. Somewhere.

        This heurestics exponentially increases and the scan chunk size depending on if we are seeing events or not.
        When any transfers are encountered we are back to scan only few blocks at the time.
        It does not make sense to do a full chain scan starting from block 1, doing one JSON-RPC call per 20 blocks.
        """

        if event_found_count > 0:
            # When we encounter first events then reset the chunk size window
            current_chuck_size = self.min_scan_chunk_size
        else:
            current_chuck_size *= self.chunk_size_increase

        current_chuck_size = max(self.min_scan_chunk_size, current_chuck_size)
        current_chuck_size = min(self.max_scan_chunk_size, current_chuck_size)
        return int(current_chuck_size)

    def update_scan_status(self, start_block, end_block):
        # Update token scan status
        status = self.get_or_create_status()
        if not status.start_block:
            status.start_block = start_block

        status.end_block = end_block
        status.end_block_timestamp = self.get_block_timestamp(status.end_block)

    def scan(self, start_block, end_block, start_chunk_size=20, progress_callback=Optional[Callable]) -> dict:
        """Perform a token balances scan.

        Assumes all balances in the database are valid before start_block (no forks sneaked in).

        :param start_block: The first block included in the scan

        :param end_block: The last block included in the scan

        :return: Address -> last balance mapping for all address balances that changed during those blocks
        """

        assert start_block <= end_block

        self.delete_potentially_forked_block_data(start_block)
        self.update_token_info()

        current_block = start_block
        updated_token_holders = set()  # Token holders that get updates

        # Scan in chunks, commit between
        chunk_size = start_chunk_size
        mutated_addresses = set()
        last_scan_duration = last_logs_found = 0
        status = self.get_or_create_status()

        while current_block <= end_block:

            # Where does our current chunk scan ends - are we out of chain yet?
            current_end = min(current_block + chunk_size, end_block)

            # Print some diagnostics to logs to try to fiddle with real world JSON-RPC API performance
            self.logger.debug("Scanning token transfers for blocks: %d - %d, chunk size %d, last chunk scan took %f, last logs found %d", current_block, current_end, chunk_size, last_scan_duration, last_logs_found)
            start = time.time()

            # Process blocks for this token over eth_getLogs
            mutated_addresses = self.scan_chunk(current_block, current_end)
            last_scan_duration = time.time() - start
            last_logs_found = len(mutated_addresses)

            # Manage the list of what addresses our scan has touched
            updated_token_holders.update(mutated_addresses)

            # Persistent the state how are along we are in the scan
            self.update_scan_status(start_block, current_end)

            # Update database on the disk
            self.dbsession.commit()

            # Print progress bar
            if progress_callback:
                progress_callback(start_block, end_block, current_block, chunk_size)

            # Try to guess who many blocks we try to fetch over eth_getLogs API next time
            chunk_size = self.estimate_next_chunk_size(chunk_size, len(mutated_addresses))

            # Set where the next chunk starts
            current_block = current_end + 1

        # Calculate balances to all accounts that have not seen new total since the last scan
        status.update_denormalised_balances()
        self.dbsession.commit()  # Write latest balances

        result = status.get_raw_balances(mutated_addresses)
        return result

