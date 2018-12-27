Install
=======

Security token interaction happens through a command line `sto` command that connects to an Ethereum network node and a local database. This command is written in Python.

.. contents:: :local:

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
