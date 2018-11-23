This is a Python package for technical corporate governance actions in TokenMarket TM-01 security framework.

The Python wrapper API describes actions for

* Issue out new stock series

* Printing out cap table

* Printing out my portfolio

* Reverting transactions

* Paying dividends

* Delivering voting ballots

In theory the APIs are backend neutral, but only EVM compatible chains are supported at the moment.

Requirements
============

* Python 3.6

* UNIX command line experience

Install
=======

Normal users
------------

Dockerised distribution is provided to all operating system.

First install Docker.

Then set up a shell alias for `board` command that we use to execute

Developers
----------

Create Python virtual env. Then install from Github::

    asdasd

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

    board ethereum-create-account

This will give you a new raw private key and related Ethereum address to play with::

    Corporate governance tool for security tokens, version 0.1 - Copyright TokenMarket Ltd. 2018
    Creating new Ethereum account.
    Account address: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Account private key: 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c8005

Now create a file `myconfig.ini` and add the content::

    # Example configuration file

    # Where to connect for Parity or Geth JSON-RPC API
    ethereum-node-url = http://localhost:8545

    # The private key for your generated Ethereum account
    ethereum-private-key = 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c8005

Visit `Kovan faucet <https://faucet.kovan.network/>`_ and request some Kovan ETH (KETH) on your account you just created.

Test that your account has balance and Parity node works::

    board diagnose

This should output::




