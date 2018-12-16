A tool and Python API for issuing out and managing out security tokens.


.. image:: https://badges.gitter.im/TokenMarketNet/sto.svg
   :alt: Join the chat at https://gitter.im/security-token/Lobby
   :target: https://gitter.im/security-token/Lobby

.. image:: https://img.shields.io/travis/TokenMarketNet/sto.svg
        :target: https://travis-ci.org/TokenMarketNet/sto

**Technical dragons ahead**

This software is for technically sophisticated users only. If you are looking for business services go to `TokenMarket commercial support <https://tokenmarket.net/security-token-offering>`_.

Table of contents
=================

.. contents::

Benefits
========

This Python package provides a command line tool and API to manage and integrate security token functionality:

* Issue out new stock series

* Printing out cap table

* Printing out my portfolio

* Managing bad transactions and lost privat keys

* Paying dividends

* Delivering voting ballots

In theory the APIs are backend neutral, but only EVM compatible chains are supported at the moment.

* `Read an introduction for security tokens <https://tokenmarket.net/news/security-tokens/what-are-security-tokens/>`_

* `View security token management source code on Github <http://github.com/tokenmarketnet/sto>`_

* `View security token management package on Python package index <https://pypi.org/project/sto/>`_

Supported networks and tokens
=============================

We currently support

* In-house Ethereum based tokens

We are looking to expand support to other networks (EOS) and other token models (Polymath) as soon as we establish proper partnerships.

Requirements
============

* Ethereum node, for example a local Parity install or Infura-node-as-a-service

* Command line tool experience

* Docker

Install
=======

Security token interaction happens through a command line `sto` command that connects to an Ethereum network node and a local database. This command is written in Python.

Normal users
------------

This tool is for command line users / developers only. `For arranging a business deal contact TokenMarket security token team <https://tokenmarket.net/security-token-offering>`_.

Advanced users
--------------

The `sto` command line application is provided as a `Docker image <https://hub.docker.com/r/miohtama/sto/>`_ to minimize the issues with painful native dependency set up for your operating system. To use `sto` we will set up a command line alias, as Docker command itself is quite long.

Install `Docker <https://www.docker.com/products/docker-desktop>`_.

OSX and Linux
~~~~~~~~~~~~~

Set up a shell alias for `sto` command that executes Dockerised binary::

    alias sto='docker run -p 8545:8545 -v `pwd`:`pwd` -w `pwd` miohtama/sto:latest'

Then you can do::

    sto --help

Docker will automatically pull an image from Docker registry for your local computer on the first run. We map port 8545 to the localhost as that is normal Ethereum JSON-RPC API.

.. image:: https://github.com/TokenMarketNet/sto/raw/master/docs/source/screenshots/help.png
    :width: 500 px

Windows
~~~~~~~

Windows PowerShell instructions coming soon.

Meanwhile use Linux instructions and `Linux Subsystem for Windows <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.

Developers
----------

Python 3.6+ required.

Create `Python virtual environment <https://packaging.python.org/tutorials/installing-packages/#optionally-create-a-virtual-environment>`_.

Then within the activated venv do::

    git clone "git+https://github.com/TokenMarketNet/sto.git"
    python -m venv venv  # Python 3 needed
    source venv/bin/activate
    pip install -U pip  # Make sure you are at least pip 18.1 - older versions will fail
    pip install -e ".[dev,test]"

How to set up
=============

Below are short instructions how to set up an Ethereum node, account and configuration file for the Kovan testnet (no real money involved).

You need an Ethereum node. You can either install yourself (see Install Parity) or use a Ethereum node provider like `Infura <https://infura.io/>`_.

Sign up for Infura (Option a)
-----------------------------

`Sign up for Infura <https://infura.io/>`_.

Get a **Kovan** node URL from your dashboard (use dropdown):

.. image:: https://github.com/TokenMarketNet/sto/raw/master/docs/source/screenshots/infura.png
    :width: 500 px

Install Parity (Option b)
-------------------------

First `install Parity <https://wiki.parity.io/Setup>`_. For example on OSX using Brew package management::

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

    Creating new Ethereum account.
    Account address: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Account private key: 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c...

Now create a file `myconfig.ini` and add the content::

    # Your personal configuration file as we told you on Github example

    # Network we are using
    network = kovan

    # This is for Parity - if you are using Infura get your Kovan node URL from your Infura dashboard
    ethereum-node-url = http://localhost:8545

    # The private key for your generated Ethereum account
    ethereum-private-key = 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c....


Top up
------

Visit `Kovan faucet <https://faucet.kovan.network/>`_.

Request Kovan ETH (KETH) on your account you just create above. A `Github account <http://github.com/>`_ is needed for verification. This should give you 1 Kovan ETH to play with and you become a testnet millionaire.

Diagnose and test run
---------------------

Use `sto diagnose` command to check your account has balance and your Ethereum node works::

    sto --config-file=myconfig.ini diagnose

This should output:

.. image:: https://github.com/TokenMarketNet/sto/raw/master/docs/source/screenshots/diagnose.png
    :width: 500 px


Playing with security tokens
============================

Issuing out stock
-----------------

Before issuing out stock you need to have set up a functional Ethereum account like described above.

To issue out stock you need to give stock name, ticker symbol and amount of shares::

    sto --config-file=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --amount=10000

You will get a list of Ethereum transactions needed to perform this operation::

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

    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ---------------------------------------------------------
    0x4bd273895b21a3b57e93113c26895ea142f989cde13ff0c23bb330de1889238a  success:9513331          70  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xc48DA079aab7FEf3a2476B493f904509d1891Fa3  Deploying unrestricted transfer policy for Doobar
    0xc5bb03a49bdc58cecb0ad36ff7f1aac84e29b08c2ed67c17d7ecab2f55d63c54  success:9513331          71  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Whitelisting deployment account for Doobar issuer control
    0xbbe0e59db71839b4b7cf7c8ac082c9204513243d3ae3ca38c98b8d443f9699ed  success:9513331          72  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Making transfer restriction policy for Doobar effective
    0x565eda7f18c9d05255b3f29c9d677734bbdb97e25d62d10d1033208030dda0a7  success:9513331          73  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Creating 10000 initial shares for Doobar


You can also enter TXID to `Kovan EtherScan explorer to see how your transactions are doing <http://kovan.etherscan.io/>`_ to check more information about your transactions.

View STO token information
--------------------------

After all your transactions have been pushed out and are succesfully included in blocks, you can view the token status by entering the contract address::

    sto --config-file=myconfig.ini token-status --address=0xa2016C64D4687Ad4184bA1dA98711e83a36eD1c2

This outputs::

    Name: Boobar
    Symbol: STO
    Total supply: 10000
    Decimals: 18
    Owner: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Transfer verified: 0x7598E970888F51d7D35468E50768Fa5F21B46Bb3


Distributing shares to investors
--------------------------------

The command line tool supports a simple CSV import to distribute shares to shareholders.

* Shares are moved to a hot wallet account, as configured above. (In the future, smart contract based and optimised distribution methods are supported.)

* `sto` reads a CSV file with investor info (see example CSV file for colums)

* Transactions are prepared for broadcasting

* Transactions are broadcasted and a log file is written

Each imported transaction must have an unique `external_id` attribute, so that we can track which distribution transaction corresponds incoming payment transaction.

First you need to record down the issued token address from above.

Example how to import CSV. `We use an example file from the source code repository <https://github.com/TokenMarketNet/sto/raw/master/docs/source/example-distribution.csv>`_::

     # Download example CSV file provided with source code repository
    curl -O https://github.com/TokenMarketNet/sto/raw/master/docs/source/example-distribution.csv

    # Your token contract address goes here
    sto --config-file=myconfig.ini distribute --csv-input=example-distribution.csv --address==0x....

This should output::

    Distribution created 2 new transactions and there was already 0 old transactions in the database

Now you can broadcast your distribution transactions with ``sto tx-broadcast``.

Verifying contracts on EtherScan
--------------------------------

`EtherScan is a popular service for blockchain exploring <https://etherscan.io>`_. It's verify contract feature allows you to create reproducible builds of your Solidity source code and then EtherScan can introspect your contract state. This is very useful for diagnostics.

To verify your contracts on EtherScan, you need to first ensure all contract deployement transactions are broadcasted and mined.

Then add your EtherScan API key in ``myconfig.ini``::

    # Obtained after signing in to etherscan.io
    etherscan-api-key = T2JC4....

Now you can run verify::

    sto --config-file=myconfig.ini tx-verify

Making a release
================

Instructions for the future-maintainers-to-be.

First send out PyPi release::


    export bump="--new-version 0.1.1 devnum"
    make release


Then push out new Docker::

    docker login --username=miohtama
    docker build -t miohtama/sto:latest .
    docker tag miohtama/sto:latest miohtama/sto:0.1.2
    docker push miohtama/sto:latest
    docker push miohtama/sto:0.1.2

Other
=====

`Ethereum smart contracts are managed in ICO repository <http://github.com/tokenmarketnet/ico>`_.



