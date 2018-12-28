Fetching token holder balances
==============================

Token holder balances ae managed in a blockchain. Accessing token holder information real time from a blockchain is non-trivial. For complex operations, like printing out the cap table, we need to crunch the blockchain data first to a local database.

``sto`` can scan the blockchain and construct a database of all past token transactions. Based on this information we can print out the cap table in any point of time.

Scanning token holders
----------------------

To scan all transactions of your security token you can do:

.. code-block:: console

    sto --config-file=myconfig.ini token-scan --token-address=0x1091aA1ED6070eDEDFdf46f665C1eD78Bd2c7431

Use the token address for which you have created a distribution.

Reruns
------

Rerunning `sto token-scan` starts from the block where it was left last time. We look back few blocks (10) to ensure that any transfers lost in minor blockchain forks are corrected.

About the scan algorithm
------------------------

The provided scan algorithm is referential in the nature. It may not scale to large number or tokens or token holders. The algorithm has been designed the limitations of SQLite databases in mind.


