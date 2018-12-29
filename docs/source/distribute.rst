Distributing shares
===================

The command line tool supports a simple CSV import to distribute shares to shareholders.

* Shares are moved to a hot wallet account, as configured above. (In the future, smart contract based and optimised distribution methods are supported.)

* `sto` reads a CSV file with investor info (see example CSV file for colums)

* Transactions are prepared for broadcasting

* Transactions are broadcasted and a log file is written

Each imported transaction must have an unique `external_id` attribute, so that we can track which distribution transaction corresponds incoming payment transaction.

First you need to record down the issued token address from above.

Example how to import CSV. `We use an example file from the source code repository <https://github.com/TokenMarketNet/sto/raw/master/docs/source/example-distribution.csv>`_:

.. code-block:: shell

     # Download example CSV file provided with source code repository
    curl -O https://github.com/TokenMarketNet/sto/raw/master/docs/source/example-distribution.csv

    # Your token contract address goes here
    sto --config-file=myconfig.ini distribute-multiple --csv-input=example-distribution.csv --address==0x....

This should output::

    Distribution created 2 new transactions and there was already 0 old transactions in the database

Now you can broadcast your distribution transactions with ``sto tx-broadcast`` (see :doc:`broadcasting <broadcast>`).


