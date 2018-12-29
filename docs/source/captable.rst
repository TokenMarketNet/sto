Cap table
=========

Cap table show the current ownership, or token holding addresses, of security tokens.

Cap table can be printed for the current moment or any moment in the past.

Cap table output may contain the real world identities of the owners, if supplied via external CSV file, or just plain Ethereum addresses.

Scanning token holders first
----------------------------

To print the cap table, first you need to build the local database of token transactions. See :doc:`token scanner <scanner>` for details.

Printing out the token holder cap table
---------------------------------------

Use ``sto cap-table`` command to print out differen views on the table.

Here we print out the cap table

Cap table for any ERC-20 token
------------------------------

``sto token-scan`` and ``sto cap-table`` command support creating token holder database of any ERC-20 token, not just security tokens. Here is a quick tutorial how to print out the token holders of `Reality Clash <https://realityclash.com>` token.

First create a INI configuration while that connects to `Infura Ethereum mainnet node <http://infura.io/>`_ or your local mainnet node.

`mainnet.ini` example:

.. code-block:: ini

    # Network we are using
    network = ethereum

    # Get this from your Infura dashboard
    ethereum-node-url = https://mainnet.infura.io/v3/453...

Then scan all RCC token transactions of all time. Please note that the scan process may take anywhere between 15 minutes to few hours depening on how fast your connection to the node and computer are.

.. code-block:: shell

    sto --config-file=mainnet.ini token-scan --token-address=0x9b6443b0fb9c241a7fdac375595cea13e6b7807a

.. note::

    Currently the scanner is not interrupt safe, so you need to let it to complete the initial scan uninterrupted.

Now you can print out the cap table. Here is how to print out top 50 token holders:

.. code-block:: shell

    sto --config-file=mainnet.init cap-table \
        --token-address=0x9b6443b0fb9c241a7fdac375595cea13e6b7807a \
        --order-by=balance \
        --order-direction=desc




