Distribute Dividends
====================

The command line tool supports a simple CSV input to make payouts to shareholders.

* If you own security tokens, you are entitled to the payouts.

* ``payout-distribute`` takes in the input csv with investor info.

* ``create-holders-payout-csv`` is an optional command that can be used to generate the CSV. This CSV contains investor with
    their respective shares. This basically fetches data by running ``token-scan`` in the background.

* Edit this csv to remove some holders or to modify the amount.

* payouts can be made either in ether or any other payable ERC20 compliant token. use `--payment-type` flag in
  ``payout-distribute`` to specify the type of payout. ``payment-type`` can either be `ether` or `token`. If ``payment-type``
  is `token` then ``payment-token-address`` and ``payment-token-symbol`` are required parameters. ``payment-token-address``
  refers to the address of the deployed payout-token and  ``payment-token-symbol`` refers to the symbol of the payout token.

* Transactions are prepared for broadcasting.

* Transactions are broadcasted and an audit log is written to the database.

Each imported transaction must have an unique `external_id` attribute, so that we can track which payout distribution transaction corresponds outgoing payment transaction.

Example of generating a csv:

.. code-block:: shell

    sto --config=myconfig.ini create-holders-payout-csv --csv-output="/Home/data/payout.csv"

This will create a csv in the specified output file.


make sure that you run the ``token-scan`` command before running ``create-holders-payout-csv``.
See how to :doc:`scan token balances and print out cap table of shareholders <scanner>`

Example for making payouts:

.. code-block:: shell

    sto --config=myconfig.ini payout-distribute --csv-input="/Home/data/payout.csv" --payment-type="ether"


This should output:


Note
----
Address(0) will be intentionally skipped from payouts, so the total amount of tokens (and their proportional value)
will not change

Next reading
------------

See how to :doc:`verifying contracts on EtherScan <etherscan>`