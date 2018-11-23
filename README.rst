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

Parity will now sync you to Kovan network using warp (fast mode). This should take 30 minutes. You can continue to follow instructions below.

Set up Ethereum account
-----------------------

To start playing with tokenised ahsers

Create an Ethereum account::

    board create-ethereum-account

This will give you the account information::


Now create a file `myconfig.ini` and add the content::

Visit `Kovan faucet <https://faucet.kovan.network/>`_ and request some Kovan ETH (KETH) on your account you just created.



