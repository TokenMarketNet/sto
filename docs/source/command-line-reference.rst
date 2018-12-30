
Command line reference
======================

Here is the command line reference for ``sto`` command.

.. contents:: :local:

Options and config files
------------------------

Settings can be either given in a config file, specified by ``--config-file`` switch or directly to the main command.

E.g. these are equivalent.

Command line:

.. code-block:: shell

    sto --ethereum-node-url="https://mainnet.infura.io/v3/453d2049c15d4a8da5501a0464fa44f8" token-scan ...
    
As with INI file ``mainnet.ini``:

.. code-block:: ini
    
    # Infura mainnet net node url
    ethereum-node-url = https://mainnet.infura.io/v3/453d2049c15d4a8da5501a0464fa44f8
    
.. code-block:: shell

    sto --config-file=mainnet.ini token-scan ...

Subcommands take their own options that cannot be specified in the settings file.
 
Main command and options
------------------------

When running ``sto --help`` you get list of settings and subcommands:

.. code-block:: text

   Usage: sto [OPTIONS] COMMAND [ARGS]...

     TokenMarket security token management tool.

     Manage tokenised equity for things like issuing out new, distributing and revoking shares.

   Options:
     --config-file PATH            INI file where to read options from
     --database-file PATH          SQLite file that persists transaction broadcast status
     --network TEXT                Network name. Either 'ethereum' or 'kovan' are supported for now.
     --ethereum-node-url TEXT      Parity or Geth JSON-RPC to connect for Ethereum network access
     --ethereum-abi-file TEXT      Solidity compiler output JSON to override default smart contracts
     --ethereum-gas-price TEXT     How many GWei we pay for gas
     --ethereum-gas-limit INTEGER  What is the transaction gas limit for broadcasts
     --ethereum-private-key TEXT   Private key for the broadcasting account
     --etherscan-api-key TEXT      EtherScan API key used for the contract source code verification
     --log-level TEXT              Python logging level to tune the verbosity of the command
     --auto-restart-nonce BOOLEAN  Automatically restart nonce for the deployment account if starting with a fresh database
     --help                        Show this message and exit.

   Commands:
     cap-table                Print out token holder cap table.
     diagnose                 Show your node and account status.
     distribute-multiple      Distribute shares to multiple shareholders whose address info is read from a file.
     distribute-single        Send tokens to one individual shareholder.
     ethereum-create-account  Creates a new Ethereum account.
     issue                    Issue out a new security token.
     issue-logs               Print out transactions of for tokens issued in the past.
     reference                Print out the command line reference for the documentation.
     token-scan               Update token holder balances from a blockchain to a local database.
     token-status             Print token contract status.
     tx-broadcast             Broadcast waiting transactions.
     tx-last                  Print latest transactions from database.
     tx-next-nonce            Print next nonce to be consumed.
     tx-restart-nonce         Resets the broadcasting account nonce.
     tx-update                Update transaction status.
     tx-verify                Verify source code of contract deployment transactions on EtherScan.



.. _cap-table:

cap-table
-------------------------------------

Print out token holder cap table.

The token holder data must have been scanned earlier using token-scan command.

You can supply optional CSV file that contains Ethereum address mappings to individual token holder names.

.. code-block:: text

    Usage: sto cap-table [OPTIONS]

      Print out token holder cap table.

      The token holder data must have been scanned earlier using token-scan
      command.

      You can supply optional CSV file that contains Ethereum address mappings
      to individual token holder names.

    Options:
      --identity-file TEXT            CSV file containing address real world
                                      identities
      --token-address TEXT            Token contract address  [required]
      --order-by [balance|name|updated|address]
                                      How cap table is sorted
      --order-direction [asc|desc]    Sort direction
      --include-empty BOOLEAN         Sort direction
      --max-entries INTEGER           Print only first N entries
      --accuracy INTEGER              How many decimals include in balance output
      --help                          Show this message and exit.




.. _diagnose:

diagnose
-------------------------------------

Show your node and account status.

.. code-block:: text

    Usage: sto diagnose [OPTIONS]

      Show your node and account status.

    Options:
      --help  Show this message and exit.




.. _distribute-multiple:

distribute-multiple
-------------------------------------

Distribute shares to multiple shareholders whose address info is read from a file.

.. code-block:: text

    Usage: sto distribute-multiple [OPTIONS]

      Distribute shares to multiple shareholders whose address info is read from
      a file.

    Options:
      --csv-input TEXT  CSV file for entities receiving tokens  [required]
      --address TEXT    Token contract address  [required]
      --help            Show this message and exit.




.. _distribute-single:

distribute-single
-------------------------------------

Send tokens to one individual shareholder.

.. code-block:: text

    Usage: sto distribute-single [OPTIONS]

      Send tokens to one individual shareholder.

    Options:
      --token-address TEXT  Token contract address  [required]
      --to-address TEXT     Receiver  [required]
      --external-id TEXT    External id string for this transaction - no
                            duplicates allowed  [required]
      --email TEXT          Receiver email (for audit log only)  [required]
      --name TEXT           Receiver name (for audit log only)  [required]
      --amount TEXT         Amount of tokens as a decimal number  [required]
      --help                Show this message and exit.




.. _ethereum-create-account:

ethereum-create-account
-------------------------------------

Creates a new Ethereum account.

.. code-block:: text

    Usage: sto ethereum-create-account [OPTIONS]

      Creates a new Ethereum account.

    Options:
      --help  Show this message and exit.




.. _issue:

issue
-------------------------------------

Issue out a new security token.

* Creates a new share series

* Allocates all new shares to the management account

* Sets the share transfer restriction mode

.. code-block:: text

    Usage: sto issue [OPTIONS]

      Issue out a new security token.

      * Creates a new share series

      * Allocates all new shares to the management account

      * Sets the share transfer restriction mode

    Options:
      --symbol TEXT                [required]
      --name TEXT                  [required]
      --amount INTEGER             [required]
      --transfer-restriction TEXT
      --help                       Show this message and exit.




.. _issue-logs:

issue-logs
-------------------------------------

Print out transactions of for tokens issued in the past.

.. code-block:: text

    Usage: sto issue-logs [OPTIONS]

      Print out transactions of for tokens issued in the past.

    Options:
      --help  Show this message and exit.




.. _reference:

reference
-------------------------------------

Print out the command line reference for the documentation.

.. code-block:: text

    Usage: sto reference [OPTIONS]

      Print out the command line reference for the documentation.

    Options:
      --help  Show this message and exit.




.. _token-scan:

token-scan
-------------------------------------

Update token holder balances from a blockchain to a local database.

Reads the Ethereum blockchain for a certain token and builds a local database of token holders and transfers.

If start block and end block information are omitted, continue the scan where we were left last time.
Scan operations may take a while.

.. code-block:: text

    Usage: sto token-scan [OPTIONS]

      Update token holder balances from a blockchain to a local database.

      Reads the Ethereum blockchain for a certain token and builds a local
      database of token holders and transfers.

      If start block and end block information are omitted, continue the scan
      where we were left last time. Scan operations may take a while.

    Options:
      --start-block TEXT    The first block where we start (re)scan
      --end-block TEXT      Until which block we scan, also can be 'latest'
      --token-address TEXT  Token contract address  [required]
      --help                Show this message and exit.




.. _token-status:

token-status
-------------------------------------

Print token contract status.

.. code-block:: text

    Usage: sto token-status [OPTIONS]

      Print token contract status.

    Options:
      --address TEXT  Token contract addrss  [required]
      --help          Show this message and exit.




.. _tx-broadcast:

tx-broadcast
-------------------------------------

Broadcast waiting transactions.

Send all management account transactions to Ethereum network.
After a while, transactions are picked up by miners and included in the blockchain.

.. code-block:: text

    Usage: sto tx-broadcast [OPTIONS]

      Broadcast waiting transactions.

      Send all management account transactions to Ethereum network. After a
      while, transactions are picked up by miners and included in the
      blockchain.

    Options:
      --help  Show this message and exit.




.. _tx-last:

tx-last
-------------------------------------

Print latest transactions from database.
    

.. code-block:: text

    Usage: sto tx-last [OPTIONS]

      Print latest transactions from database.

    Options:
      --limit INTEGER  How many transactions to print
      --help           Show this message and exit.




.. _tx-next-nonce:

tx-next-nonce
-------------------------------------

Print next nonce to be consumed.

.. code-block:: text

    Usage: sto tx-next-nonce [OPTIONS]

      Print next nonce to be consumed.

    Options:
      --help  Show this message and exit.




.. _tx-restart-nonce:

tx-restart-nonce
-------------------------------------

Resets the broadcasting account nonce.

.. code-block:: text

    Usage: sto tx-restart-nonce [OPTIONS]

      Resets the broadcasting account nonce.

    Options:
      --help  Show this message and exit.




.. _tx-update:

tx-update
-------------------------------------

Update transaction status.

Connects to Ethereum network, queries the status of our broadcasted transactions.
Then print outs the still currently pending transactions or freshly mined transactions.

.. code-block:: text

    Usage: sto tx-update [OPTIONS]

      Update transaction status.

      Connects to Ethereum network, queries the status of our broadcasted
      transactions. Then print outs the still currently pending transactions or
      freshly mined transactions.

    Options:
      --help  Show this message and exit.




.. _tx-verify:

tx-verify
-------------------------------------

Verify source code of contract deployment transactions on EtherScan.

Users EtherScan API to verify all deployed contracts from the management account.

.. code-block:: text

    Usage: sto tx-verify [OPTIONS]

      Verify source code of contract deployment transactions on EtherScan.

      Users EtherScan API to verify all deployed contracts from the management
      account.

    Options:
      --help  Show this message and exit.


