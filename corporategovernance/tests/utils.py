import warnings

from populus.utils.wait import wait_for_transaction_receipt


def check_gas(chain, txid: str, gaslimit=5000000, timeout=180, tag="") -> int:
    """Check if used gas is under our gaslimit, default if 5 million.
    At the time of writing the block gas just rose to 8 million 22 seconds ago
    (block 5456319, gas limit 8,003,865)"""

    # http://ethereum.stackexchange.com/q/6007/620
    receipt = wait_for_transaction_receipt(chain.web3, txid, timeout=timeout)

    if (tag):
        warnings.warn(UserWarning(tag, receipt["gasUsed"], receipt["blockNumber"]))

    assert receipt["gasUsed"] < gaslimit

    return receipt["gasUsed"]