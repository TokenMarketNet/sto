This is a tool and Python API for issuing out and managing out security tokens.

.. contents:: :local:

.. note::

    This software is totally alpha. If you are do not have technical sophistication and you are not willing to sit out in a chat room to wait answer for your questions this is not for your do-it-yourself needs. Instead, contact to `TokenMarket commercial support <https://tokenmarket.net/security-token-offering>`_.


Benefits
========

The tool and API gives technical developers ability to manage and integrate security token functionality:

* Issue out new stock series

* Printing out cap table

* Printing out my portfolio

* Reverting transactions

* Paying dividends

* Delivering voting ballots

In theory the APIs are backend neutral, but only EVM compatible chains are supported at the moment.

* [Read an introduction for security tokens](https://tokenmarket.net/news/security-tokens/what-are-security-tokens/)

Supported networks and tokens
=============================

We currently support

* In-house Ethereum based tokens

We are looking to expand support to other networks (EOS) and other token models (Polymath) as soon as we establish proper partnerships.

Requirements
============

* Python 3.6

* UNIX command line experience

Install
=======

Normal users
------------

.. warning::

    Normal user instructions are not yet available. Please refer to developer instructions.

Developers
----------

Create `Python virtual environment <https://packaging.python.org/tutorials/installing-packages/#optionally-create-a-virtual-environment>`.

Then within the activated venv do::

    pip install -e "git+https://github.com/TokenMarketNet/sto.git#egg=sto"

How to set up
=============

Below are short instructions how to set up an Ethereum node, account and configuration file for a testnet (no real money involved) to test out tokens.

Set up Parity
-------------

First install geth or Parity. For example on OSX::

    brew install parity

Start Parity in another terminal and connect it to Kovan test network::

    parity --chain=kovan

Parity will now sync you to Kovan network using warp (fast mode). This will take up to two hours. You can continue to follow instructions below.

Set up Ethereum account
-----------------------

To start playing with tokenised ahsers

Create an Ethereum account::

    sto ethereum-create-account

This will give you a new raw private key and related Ethereum address to play with::

    Corporate governance tool for security tokens, version 0.1 - Copyright TokenMarket Ltd. 2018
    Creating new Ethereum account.
    Account address: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Account private key: 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c...

Now create a file `myconfig.ini` and add the content::

    # Your personal configuration file as we told you on Github example

    # "kovan" or "ethereum"
    network = kovan

    # Where to connect for Parity or Geth JSON-RPC API
    ethereum-node-url = http://localhost:8545

    # The private key for your generated Ethereum account
    ethereum-private-key = 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c....

Visit `Kovan faucet <https://faucet.kovan.network/>`_ and request some Kovan ETH (KETH) on your account you just created.

Test that your account has balance and Parity node works::

    sto diagnose

This should output::

    Corporate governance tool for security tokens, version 0.1 - Copyright TokenMarket Ltd. 2018
    Attempting to connect to Ethereum node http://localhost:8545
    Connected to Ethereum node software Parity-Ethereum//v2.1.6-stable-491f17f-20181114/x86_64-macos/rustc1.30.1
    Current Ethereum node block number: 9462884, last block 2 seconds ago
    Using private key 3fa...
    Address 0xDE5bC059aA433D72F25846bdFfe96434b406FA85 has ETH balance of 1.000000
    All systems ready to fire

Issuing out stock
-----------------

Before issuing out stock you need to have set up a functional Ethereum account like described above.

To issue out stock you need to give stock name, ticker symbol and amount of shares::

    sto --config-file=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --amount=10000

Pushing Ethereum transactions out
---------------------------------

Ethereum transactions are first written to a local `SQlite database <https://www.sqlite.org/index.html>`_. A separate step of broadcasting transactions is needed in order to write the data to Ethereum blockchain.

To broadcast::

    sto --config-file=myconfig.ini tx-broadcast

Transactions are send out to Ethereum network and they get a transaction id.

Checking out transaction status
-------------------------------

Blockchain transactions are asynchronous. First the transactions are broadcasted to the network. The transactions propagade from a node to a node until a miner node decides to include your transactions in a block.

To check your transaction status::

    sto --config-file=myconfig.ini tx-update

You can also enter TXID to `Kovan EtherScan explorer to see how your transactions are doing <http://kovan.etherscan.io/>`_ to check more information about your transactions.

Other
=====

`Ethereum smart contracts are managed in ICO repository <http://github.com/tokenmarketnet/ico>`_.



