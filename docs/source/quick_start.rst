Quickstart
==========

To get start see how to :doc:`install sto tool <install>`

Tutorial
--------

In this tutorial, we deploy the security token, distribute the tokens as per the csv and then distribute the payout to shareholders.

1. Deploy all the necessary smart contracts

.. code-block:: shell

    sto --network=kovan --ethereum-private-key=9CB5.. --ethereum-node-url="https://kovan.infura.io/v3/6b70887f1b0d4ce5bb41514e3b494936" issue --symbol=STO --name="Mikko's magic corp" --amount=10000 --url="https://tokenmarket.net"

This will output::

    Initializing new database /Users/voith/Projects/sto/transactions.sqlite
    Automatically fetching the initial nonce for the deployment account from blockchain
    Address 0xb85f30B1bA4513D1260B229348955d5497CcB55e, nonce is now set to 47
    Prepared transactions for broadcasting for network kovan
    STO token contract address will be 0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8
    TXID    Status and block      Nonce  From                                        To                                          Note
    ------  ------------------  -------  ------------------------------------------  ------------------------------------------  ----------------------------------------------------------------
            waiting                  47  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Deploying token contract for Mikko's magic corp
            waiting                  48  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xF35FDe300dbDFFc30508899bcc33112C77098C75  Deploying unrestricted transfer policy for Mikko's magic corp
            waiting                  49  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Making transfer restriction policy for Mikko's magic corp effect
            waiting                  50  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Creating 10000 initial shares for Mikko's magic corp
    Run sto tx-broadcast to write this to blockchain

2. Broadcast transactions on the ethereum network

.. code-block:: shell

    sto --network=kovan --ethereum-private-key=9CB5.. --ethereum-node-url='https://kovan.infura.io/v3/6b70887f1b0d4ce5bb41514e3b494936' tx-broadcast

This will output::

    Pending 4 transactions for broadcasting in network kovan
    Our address 0xb85f30B1bA4513D1260B229348955d5497CcB55e has ETH balance of 2.974894 for operations
    100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 4/4 [00:02<00:00,  1.43it/s]
    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ----------------------------------------------------------------
    0x30a46d2bc9492992c390e5590fa1d1baf7d0fb9458c6b2f178f4a7071ea5bb5c  broadcasted              47  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Deploying token contract for Mikko's magic corp
    0x8e3b452686d22cfce664a85c610148fb4a6d90334a10f51eba6547510b66a6b0  broadcasted              48  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xF35FDe300dbDFFc30508899bcc33112C77098C75  Deploying unrestricted transfer policy for Mikko's magic corp
    0x357cca0fa9e6cbc4c01fcb636966d7f5e0587811fa030e2f900f6d1d1de3bbd1  broadcasted              49  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Making transfer restriction policy for Mikko's magic corp effect
    0x780bd29793959f4779cb1a8f426443600d2074dd2780f37999123786348a962d  broadcasted              50  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Creating 10000 initial shares for Mikko's magic corp

3. Check the status of broadcasted transactions. You might have to run this several times until all transactions are mined

.. code-block:: shell

    sto --network=kovan --ethereum-private-key=9CB5... --ethereum-node-url='https://kovan.infura.io/v3/6b70887f1b0d4ce5bb41514e3b494936' tx-update

On successful mining, this will output::

    Updating status for 4 unfinished transactions for broadcasting in network kovan
    100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 4/4 [00:01<00:00,  2.05it/s]
    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ----------------------------------------------------------------
    0x30a46d2bc9492992c390e5590fa1d1baf7d0fb9458c6b2f178f4a7071ea5bb5c  success:10415952         47  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Deploying token contract for Mikko's magic corp
    0x8e3b452686d22cfce664a85c610148fb4a6d90334a10f51eba6547510b66a6b0  success:10415956         48  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xF35FDe300dbDFFc30508899bcc33112C77098C75  Deploying unrestricted transfer policy for Mikko's magic corp
    0x357cca0fa9e6cbc4c01fcb636966d7f5e0587811fa030e2f900f6d1d1de3bbd1  success:10415957         49  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Making transfer restriction policy for Mikko's magic corp effect
    0x780bd29793959f4779cb1a8f426443600d2074dd2780f37999123786348a962d  success:10415958         50  0xb85f30B1bA4513D1260B229348955d5497CcB55e  0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8  Creating 10000 initial shares for Mikko's magic corp

4. Distribute the tokens.

.. code-block:: shell

    # Download example CSV file provided with source code repository
    curl -O "https://raw.githubusercontent.com/TokenMarketNet/sto/master/docs/source/example-distribution.csv"

    sto --network=kovan --ethereum-private-key=9CB5.. --ethereum-node-url='https://kovan.infura.io/v3/6b70887f1b0d4ce5bb41514e3b494936' distribute-multiple --address="0x.." --csv-input="example-distribution.csv"

This will output::

    Reading CSV input example-distribution.csv
    Starting creating distribution transactions for 0xa79F4b65cf6023b9A5978541D62565CE2b6dE9b8 token from nonce 51
    100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  3.71it/s]
    Prepared transactions for broadcasting for network kovan
    Distribution created 2 new transactions and there was already 0 old transactions in the database

5. Repeat step 2 and 3.

6. Create csv to distribute payouts.

.. code-block:: shell

    sto --network=kovan --ethereum-private-key=9CB5... --ethereum-node-url='https://kovan.infura.io/v3/6b70887f1b0d4ce5bb41514e3b494936' create-holders-payout-csv --token-address="0xa.."

This will output::

    Scanning token: None
    Current last block for chain kovan: 10415993
    Scanning blocks: 1 - 10415993
    Scanning block: 10390648, batch size: 500000: : 10890620it [00:27, 103312.41it/s]
    create payout.csv

7. Distribute the payouts.

.. code-block:: shell

    sto --network=kovan --ethereum-private-key=9CB5... --ethereum-node-url='https://kovan.infura.io/v3/6b70887f1b0d4ce5bb41514e3b494936' --ethereum-gas-limit=8000000 --ethereum-gas-price=2000000000 payout-distribute --security-token-address="0xa.." --csv-input='payout.csv' --total-amount=1000000000000000000

This will output::

    Reading CSV input payout.csv
      0%|                                                                                                                                                                                                                   | 0/3 [00:00<?, ?it/s]ignoring address: 0xb85f30B1bA4513D1260B229348955d5497CcB55e as it is the same address used to distribute tokens
    100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 3/3 [00:00<00:00, 97.53it/s]
    Prepared transactions for broadcasting for network kovan
    Distribution created 2 new transactions and there was already 0 old transactions in the database

8. Repeat step 2 and 3.

9. Verify on etherscan that ether has been sent to accounts mentioned in example-distribution.csv
