======================
Dividends and interest
======================

Introduction
============

Dividends, interest or royalties can be generally lumped together as payouts.
We support doing

* Dumb payouts: wiring stable coins directly to the owner address

* Payout contract:


Payout contract

The Payout contract provides the ability to set up dividend distribution.


Distribute Dividends
====================

The command line tool supports a simple CSV input to make payouts to shareholders.

* If you own security tokens, you are entitled to the payouts.

* ``payout-distribute`` takes in the input csv with investor info.

* ``create-holders-payout-csv`` is an optional command that can be used to generate the CSV. This CSV contains investor with
    their respective shares. This basically fetches data by running ``token-scan`` in the background.

* Edit this csv to suit your needs.

* payouts can be made either in ether or any other payable ERC20 compliant token. use `--payment-type` flag in
  ``payout-distribute`` to specify the type of payout. ``payment-type`` can either be `ether` or `token`. If ``payment-type``
  is `token` then ``payment-token-address`` is a required parameter. ``payment-token-address``
  refers to the address of the deployed payout-token.

* Transactions are prepared for broadcasting.

* Transactions are broadcasted and an audit log is written to the database.

Each imported transaction must have an unique `external_id` attribute, so that we can track which payout distribution transaction corresponds outgoing payment transaction.

Example of generating a csv:

.. code-block:: shell

    sto --config=myconfig.ini create-holders-payout-csv --csv-output="/Home/data/payout.csv"

This will create a csv in the specified output file.


make sure that you run the ``token-scan`` command before running ``create-holders-payout-csv``.
See how to :doc:`scan token balances and print out cap table of shareholders <scanner>`

Example for making payouts in ether:

.. code-block:: shell

    sto --config=myconfig.ini payout-distribute --csv-input="/Home/data/payout.csv" --total-amount=10000000 --payment-type="ether"

The total amount needs to be in wei.

Example for making payouts in tokens:
.. code-block:: shell

    sto --config=myconfig.ini payout-distribute --csv-input="/Home/data/payout.csv" --total-amount=10000000 --payment-type="token" --payout_token_address="0x..."


This should output:
    Run <sto tx-broadcast> to broadacst your transactions on the blockchain

See how to :doc:`broadcast transaction on ethereum <broadcast>`

Note
----
Address(0) will be intentionally skipped from payouts, so the total amount of tokens (and their proportional value)
will not change

Next reading
------------

See how to :doc:`verify contracts on EtherScan <etherscan>`


Payout Deploy
-------------

To deploy the payout smart contract::

    sto --config=myconfig.ini payout-deploy --token-address="0x.." --payout-token-address="0x.." --payout-token-name="CrowdsaleToken" --kyc-address="0x.." --payout-name='Pay X' --uri="http://tokenmarket.net" --type=0

- ``--token-address`` is the address of the deployed security token.
- ``--payout-token-address`` is the address token used in paying out.
- ``--payout-token-name`` is the name of the payout token. This should be the same name as defined in the smart contract.
- ``--kyc-address`` is the address of the deployed kyc smart contract.
- ``--payout-name`` is the name you want to give to your Payout smart contract
- ``--uri`` uri used for announcement
- ``--type`` used in announcement smart contract

Payout Approve
--------------

In order to release token to the Payout smart contract, they first need to be approved. This should only be run once::

    sto --config=myconfig.ini payout-approve --payout-token-name="CrowdsaleToken"


``--payout-token-name`` name of the payout_token used earlier to deploy payout smart contract.


Payout deposit
--------------

To fetch the approved tokens call command::

    sto --config=myconfig.ini payout-deposit
