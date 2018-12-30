Cap table for any ERC-20 token
==============================

``sto token-scan`` and ``sto cap-table`` command support creating token holder database of any ERC-20 token, not just security tokens or tokens you have issued yourself. If you need to use token holder or transfer data in your application you can read it directly from ``sto`` SQLite database.

.. note::

   As most of the ERC-20 tokens are payment terms, using term cap table is little bit misleading.
   The term "token holders" is more generic.

Preparing and printing out token holders
----------------------------------------

Here is a quick tutorial how to print out the token holders of `Reality Clash <https://realityclash.com>`_ token.

First create a INI configuration while that connects to `Infura Ethereum mainnet node <http://infura.io/>`_ or your local mainnet node.

``mainnet.ini`` example`:

.. code-block:: ini

    # Network we are using
    network = ethereum

    # Get this from your Infura dashboard
    ethereum-node-url = https://mainnet.infura.io/v3/453...

Then scan all RCC token transactions of all time. Please note that the scan process may take anywhere between 15 minutes to few hours depening on how fast your connection to the node and computer are.

.. code-block:: shell

    sto --config-file=mainnet.ini token-scan --token-address=0x9b6443b0fb9c241a7fdac375595cea13e6b7807a

.. image:: screenshots/scan-reality-clash.png
    :width: 500 px

.. note::

    If the scan is interrupted it will pick up where it was left last time. You can also manually interrupt the application with CTRL+C.

Now you can print out the cap table. Here is how to print out top 10 token holders:

.. code-block:: shell

    sto --config-file=mainnet.init cap-table \
        --token-address=0x9b6443b0fb9c241a7fdac375595cea13e6b7807a \
        --order-by=balance \
        --order-direction=desc \
        --max-entries=10

And it prints out the RCC top holders table:

.. image:: screenshots/rcc-captable.png
    :width: 500 px
