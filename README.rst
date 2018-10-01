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

* Senior Python software development experience

Running tests locally
=====================

You need to set up a contracts repository symlinks as following::

    ln -s ../ico/zeppelin .
    ln -s ../zeppelin/contracts .

Set up used solc version for your shell::

    export SOLC_VERSION=0.4.18
    export SOLC_BINARY=$(pwd)/../ico/dockerized-solc.sh

First test that all contracts compile::

    populus compile

Then run tests::

    tox
