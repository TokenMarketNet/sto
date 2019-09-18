How to set up and first run
===========================

Below are short instructions how to set up an Ethereum node, account and configuration file for the Kovan testnet (no real money involved).

You need an Ethereum node. You can either install yourself (see Install Parity) or use a Ethereum node provider like `Infura <https://infura.io/>`_.

.. contents:: :local:

Sign up for Infura (Option a)
-----------------------------

`Sign up for Infura <https://infura.io/>`_.

Get a **Kovan** node URL from your dashboard (use dropdown):

.. image:: screenshots/infura.png
    :width: 500 px

Install Parity (Option b)
-------------------------

First `install Parity <https://wiki.parity.io/Setup>`_. For example on OSX using Brew package management:

.. code-block:: console

    brew install parity

Start Parity in another terminal and connect it to Kovan test network:

.. code-block:: console

    parity --chain=kovan

Parity will now sync you to Kovan network using warp (fast mode). This will take up to two hours. You can continue to follow instructions below.

Sign up for QuikNode (Option c)
-----------------------------

`Sign up for QuikNode <https://quiknode.io/>`_.

Get a **Kovan** node on Parity and use the Web3 URL from your dashboard (Dev Tools):

.. image:: screenshots/quiknode.png
    :width: 500 px


Set up Ethereum account
-----------------------

To start playing with tokenised shares we first need to create a new Ethereum account we use for management operations.

Create an Ethereum account::

    sto --network=kovan ethereum-create-account

This will give you a new raw private key and related Ethereum address to play with:

.. code-block:: text

    Creating new Ethereum account.
    Account address: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Account private key: 3fac35a57e1e2867290ae37d54c5de61d52644b42819ce6af0c5a9c25f4c...

Now create a file `myconfig.ini` and add the content:

.. code-block:: ini

    # Your personal configuration file as we told you on Github example

    # Network we are using
    network = kovan

    # This is for Parity - if you are using Infura or QuikNode get your Kovan node URL from your dashboard
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

    sto --config=myconfig.ini diagnose

This should output:

.. image:: screenshots/diagnose.png
    :width: 500 px

Now your can proceed to :doc:`issue out your first play shares <issuance>`.

