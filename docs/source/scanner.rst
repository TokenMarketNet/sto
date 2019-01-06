Fetching token holder balances
==============================

Token holder balances ae managed in a blockchain. Accessing token holder information real time from a blockchain is non-trivial. For complex operations, like printing out the cap table, we need to crunch the blockchain data first to a local database.

``sto`` can scan the blockchain and construct a database of all past token transactions. Based on this information we can print out the cap table in any point of time.

Scanning token holders
----------------------

To scan all transactions of your security token use ``token-scan`` command. Use the token address for which you have created a distribution.

.. code-block:: console

    sto --config=myconfig.ini token-scan --token-address=0x1091aA1ED6070eDEDFdf46f665C1eD78Bd2c7431

Scan may take few minutes, as the operation walks through the whole blockchian. In the end, it should print:

.. code-block:: text

    Scanning token: Mikko's corp 5
    Current last block for chain kovan: 9880112
    Scanning blocks: 133739 - 9880112
    Last scan ended at block: 133749
    Scanning block: 9524384, batch size: 500000: : 9890620it [00:13, 104737.39it/s]
    Updated 3 token holder balances

Reruns
------

Rerunning `sto token-scan` starts from the block where it was left last time. We look back few blocks (10) to ensure that any transfers lost in minor blockchain forks are corrected.

About the scan algorithm
------------------------

The provided scan algorithm is referential in the nature. It may not scale to large number or tokens or token holders. The algorithm has been designed the limitations of SQLite databases in mind.

Printing to cap table
---------------------

After you have scanned the balances you can :doc:`print the cap table <captable>`.

Further information
-------------------

See :ref:`token-scan` command.
