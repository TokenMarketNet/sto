Broadcasting transactions
=========================

Ethereum transactions are first written to a local `SQlite database <https://www.sqlite.org/index.html>`_. A separate step of broadcasting transactions is needed in order to write the data to Ethereum blockchain. Furthermore local database allows us to add human friendly annotations for transactions, so that diagnostics and future audits are easy.

Using a local database and locally generated nonces ensures we can always safely rebroadcast transactions and issue out new transactions even under severe network conditions.

To broadcast::

    sto --config=myconfig.ini tx-broadcast

Transactions are send out to Ethereum network and they get a transaction id. You will see `txid` in output::

    Pending 5 transactions for broadcasting in network kovan
    Our address 0xDE5bC059aA433D72F25846bdFfe96434b406FA85 has ETH balance of 0.955684 for operations
    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ---------------------------------------------------------
    0x6bb9755f492f9d4497457df0da8cfd91ab32efaad7bb67444f4e2e00351e9427  broadcasted              74  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Deploying token contract for Moobar
    0xefd6ad3b3c8a8364b315b6c73667baf6d657493d8dad14423b41a32b22444d60  broadcasted              75  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x533FeDE8F86C3e8a7923fEa4f55007f25AF5db30  Deploying unrestricted transfer policy for Moobar
    0x4d31a1d15c1f479c48a21798f5d81d275b34b3fa8cbf9e450dc2ad20b0001e41  broadcasted              76  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Whitelisting deployment account for Moobar issuer control
    0xe45a64c71a42100858b9880c40a59e7728fb4c5a11adf14ff509323fc08f21de  broadcasted              77  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Making transfer restriction policy for Moobar effective
    0x948b9925f8afe134b39e8c3384c51e0027c839a9737b6307ab77419992b293c7  broadcasted              78  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xdaE00e2fbD21924443e133E14A9206CeDC046824  Creating 10000 initial shares for Moobar
    Run sto tx-update to monitor your transaction propagation status

Update transaction status
-------------------------

Blockchain transactions are asynchronous. First the transactions are broadcasted to the network. The transactions propagade from a node to a node until a miner node decides to include your transactions in a block.

`tx-update` command will read tranactions from network and update the local database for pending transasctions. It will also detect if a transaction has failed e.g. due to smart contract permission errors.

To check your transaction status::

    sto --config=myconfig.ini tx-update

After a while repeating this command you should see all your transactions included in blockchain with `success` status::

    TXID                                                                Status and block      Nonce  From                                        To                                          Note
    ------------------------------------------------------------------  ------------------  -------  ------------------------------------------  ------------------------------------------  ---------------------------------------------------------
    0x4bd273895b21a3b57e93113c26895ea142f989cde13ff0c23bb330de1889238a  success:9513331          70  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xc48DA079aab7FEf3a2476B493f904509d1891Fa3  Deploying unrestricted transfer policy for Doobar
    0xc5bb03a49bdc58cecb0ad36ff7f1aac84e29b08c2ed67c17d7ecab2f55d63c54  success:9513331          71  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Whitelisting deployment account for Doobar issuer control
    0xbbe0e59db71839b4b7cf7c8ac082c9204513243d3ae3ca38c98b8d443f9699ed  success:9513331          72  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Making transfer restriction policy for Doobar effective
    0x565eda7f18c9d05255b3f29c9d677734bbdb97e25d62d10d1033208030dda0a7  success:9513331          73  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0xC423aCf9757c25048E0f10F21A4eC6a1322b4299  Creating 10000 initial shares for Doobar


You can also enter TXID to `Kovan EtherScan explorer to see how your transactions are doing <http://kovan.etherscan.io/>`_ to check more information about your transactions.

After you have get your transactions to Ethereum blockchain, see :doc:`how to view the token summary <token-summary>`.

Further information
-------------------

See :ref:`tx-broadcast` or :ref:`tx-update` commands.