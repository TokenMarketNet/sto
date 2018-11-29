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

    sto --network=kovan ethereum-create-account

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

    sto --config-file=myconfig.ini diagnose

This should output::

    Attempting to connect to Ethereum node http://localhost:8545
    Connected to Ethereum node software Parity-Ethereum//v2.1.6-stable-491f17f-20181114/x86_64-macos/rustc1.30.1
    Current Ethereum node block number: 9462884, last block 2 seconds ago
    Using private key 3fa...
    Address 0xDE5bC059aA433D72F25846bdFfe96434b406FA85 has ETH balance of 1.000000
    All systems ready to fire


Playing with security tokens
============================

Issuing out stock
-----------------

Before issuing out stock you need to have set up a functional Ethereum account like described above.

To issue out stock you need to give stock name, ticker symbol and amount of shares::

    sto --config-file=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --amount=10000

You will get a list of Ethereum transactions needed to perform this operation::

    STO tool, version 0.1 - Copyright TokenMarket Ltd. 2018
    Using database /Users/moo/code/tm2/sto/transactions.sqlite
    Prepared transactions for broadcasting for network kovan
    TXID    Status      Nonce  From                                        To                                          Note
    ------  --------  -------  ------------------------------------------  ------------------------------------------  --------------------------------------------------------------
            waiting         1  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Token contract for Mikko's magic corp
            waiting         2  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x1abECD8dF601e6e56eca99Ec1F1c50eEAe61B289  Unrestricted transfer manager for Mikko's magic corp
            waiting         3  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Setting security token transfer manager for Mikko's magic corp
            waiting         4  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Creating 10000 initial shares for Mikko's magic corp


Pushing Ethereum transactions out
---------------------------------

Ethereum transactions are first written to a local `SQlite database <https://www.sqlite.org/index.html>`_. A separate step of broadcasting transactions is needed in order to write the data to Ethereum blockchain. Furthermore local database allows us to add human friendly annotations for transactions, so that diagnostics and future audits are easy.

Using a local database and locally generated nonces ensures we can always safely rebroadcast transactions and issue out new transactions even under severe network conditions.

To broadcast::

    sto --config-file=myconfig.ini tx-broadcast

Transactions are send out to Ethereum network and they get a transaction id. You will see `txid` in output::

    Using database /Users/moo/code/tm2/sto/transactions.sqlite
    Pending 5 transactions for broadcasting in network kovan
    Our address 0xDE5bC059aA433D72F25846bdFfe96434b406FA85 has ETH balance of 0.955684 for operations
    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ---------------------------------------------------------
    0x6bb9755f492f9d4497457df0da8cfd91ab32efaad7bb67444f4e2e00351e9427  broadcasted              74  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Deploying token contract for Moobar
    0xefd6ad3b3c8a8364b315b6c73667baf6d657493d8dad14423b41a32b22444d60  broadcasted              75  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x533FeDE8F86C3e8a7923fEa4f55007f25AF5db30  Deploying unrestricted transfer policy for Moobar
    0x4d31a1d15c1f479c48a21798f5d81d275b34b3fa8cbf9e450dc2ad20b0001e41  broadcasted              76  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Whitelisting deployment account for Moobar issuer control
    0xe45a64c71a42100858b9880c40a59e7728fb4c5a11adf14ff509323fc08f21de  broadcasted              77  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Making transfer restriction policy for Moobar effective
    0x948b9925f8afe134b39e8c3384c51e0027c839a9737b6307ab77419992b293c7  broadcasted              78  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Creating 10000 initial shares for Moobar
    Run sto tx-update to monitor your transaction propagation status

Update transaction status
-------------------------

Blockchain transactions are asynchronous. First the transactions are broadcasted to the network. The transactions propagade from a node to a node until a miner node decides to include your transactions in a block.

`tx-update` command will read tranactions from network and update the local database for pending transasctions. It will also detect if a transaction has failed e.g. due to smart contract permission errors.

To check your transaction status::

    sto --config-file=myconfig.ini tx-update

After a while repeating this command you should see all your transactions included in blockchain with `success` status::

    STO tool, version 0.1 - Copyright TokenMarket Ltd. 2018
    Using database /Users/moo/code/tm2/sto/transactions.sqlite
    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ---------------------------------------------------------
    0x4bd273895b21a3b57e93113c26895ea142f989cde13ff0c23bb330de1889238a  success:9513331          70  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xc48DA079aab7FEf3a2476B493f904509d1891Fa3  Deploying unrestricted transfer policy for Doobar
    0xc5bb03a49bdc58cecb0ad36ff7f1aac84e29b08c2ed67c17d7ecab2f55d63c54  success:9513331          71  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Whitelisting deployment account for Doobar issuer control
    0xbbe0e59db71839b4b7cf7c8ac082c9204513243d3ae3ca38c98b8d443f9699ed  success:9513331          72  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Making transfer restriction policy for Doobar effective
    0x565eda7f18c9d05255b3f29c9d677734bbdb97e25d62d10d1033208030dda0a7  success:9513331          73  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Creating 10000 initial shares for Doobar


You can also enter TXID to `Kovan EtherScan explorer to see how your transactions are doing <http://kovan.etherscan.io/>`_ to check more information about your transactions.

View STO token information
--------------------------

After all your transactions have been pushed out and are succesfully included in blocks, you can view the token status::

    sto --config-file=myconfig.ini token-status --address=0xa2016C64D4687Ad4184bA1dA98711e83a36eD1c2

This outputs::

    STO tool, version 0.1 - Copyright TokenMarket Ltd. 2018
    Using database /Users/moo/code/tm2/sto/transactions.sqlite
    Name: Boobar
    Symbol: STO
    Total supply: 10000
    Decimals: 18
    Owner: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Transfer verified: 0x7598E970888F51d7D35468E50768Fa5F21B46Bb3


Other
=====

`Ethereum smart contracts are managed in ICO repository <http://github.com/tokenmarketnet/ico>`_.



