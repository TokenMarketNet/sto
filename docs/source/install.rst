Installation
============

Security token interaction happens through a command line `sto` command that connects to an Ethereum network node and a local database. `sto` command is automatically installed via Docker.

.. contents:: :local:

Requirements
------------

Skills needed

* Command line usage experience

Software or services needed

* Ethereum node, for example a local Parity installation or Infura-node-as-a-service - see :doc:`how to install <setup>`

* Docker

Normal users
------------

This tool is for command line users and developers only. We do not provide an end user application as open source. `For a managed service please contact TokenMarket business representatives <https://tokenmarket.net/security-token-offering>`_.

Advanced users
--------------

The `sto` command line application is provided as a `Docker image <https://hub.docker.com/r/miohtama/sto/>`_ to minimize the issues with painful native dependency set up for your operating system. To use `sto` we will set up a command line alias, as Docker command itself is quite long.

Install `Docker <https://www.docker.com/products/docker-desktop>`_.

OSX and Linux
~~~~~~~~~~~~~

Set up a shell alias for `sto` command that executes Dockerised binary:

.. code-block:: shell

    alias sto='docker run -p 8545:8545 -v `pwd`:`pwd` -w `pwd` miohtama/sto:latest'

Then you can do:

.. code-block:: shell

    sto --help

Docker will automatically pull an image from Docker registry for your local computer on the first run. We map port 8545 to the localhost as that is normal Ethereum JSON-RPC API.

.. image:: https://github.com/TokenMarketNet/sto/raw/master/docs/source/screenshots/help.png
    :width: 500 px

After installing see :doc:`how to set up the software <setup>`.

Windows
~~~~~~~

Windows PowerShell instructions coming soon.

Meanwhile use Linux instructions and `Linux Subsystem for Windows <https://docs.microsoft.com/en-us/windows/wsl/install-win10>`_.

Developers
----------

Python 3.6+ required.

Create `Python virtual environment <https://packaging.python.org/tutorials/installing-packages/#optionally-create-a-virtual-environment>`_.

Then within the activated venv do:

.. code-block:: shell

    git clone "git+https://github.com/TokenMarketNet/sto.git"
    python -m venv venv  # Python 3 needed
    source venv/bin/activate
    pip install -U pip  # Make sure you are at least pip 18.1 - older versions will fail
    pip install -e ".[dev,test]"
