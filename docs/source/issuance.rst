Issuing out security tokens
===========================

Before issuing out stock you need to have set up :doc:`a functional Ethereum account set up <setup>`.

To issue out stock you need to give stock name, ticker symbol and amount of shares::

    sto --config=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --url="https://tokenmarket.net" --amount=10000

You will get a list of Ethereum transactions needed to perform this operation::

    Prepared transactions for broadcasting for network kovan
    TXID    Status      Nonce  From                                        To                                          Note
    ------  --------  -------  ------------------------------------------  ------------------------------------------  --------------------------------------------------------------
            waiting         1  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Token contract for Mikko's magic corp
            waiting         2  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x1abECD8dF601e6e56eca99Ec1F1c50eEAe61B289  Unrestricted transfer manager for Mikko's magic corp
            waiting         3  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Setting security token transfer manager for Mikko's magic corp
            waiting         4  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Creating 10000 initial shares for Mikko's magic corp

Next see how to :doc:`broadcast created transactions <broadcast>`.

Issuing tokens in restricted mode
----------------------------------

The security token can deployed with `--transfer-restriction`. The default value of this flag is `unrestricted`.
When `--transfer-restriction="restricted"` the restricted mode is enabled. In restricted mode the user address should be
whitelisted in a KYC smart contract. See :doc:`How to whitelist an address <whitelist>` For more info on whitelisting.
sto --config=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --url="https://tokenmarket.net" --amount=10000


Tutorial for issuing tokens in restricted mode
----------------------------------------------
1. Deploy the KYC smart contract::

    sto --config=myconfig.ini kyc-deploy

2. WhiteList the address that will be used to deploy the `SecurityToken` smart contract. This is needed so that the
   initial balance is set correctly in the security token. If owner address is not whitelisted then security will have
   initial balance of zero. To whitelist the address::

    sto --config=myconfig.ini kyc-manage --whitelist-address='Address_that_will_be_used_to_deploy_security_token'


3. Deploy the security token smart contract::

    sto --config=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --url="https://tokenmarket.net" --amount=10000 --transfer-restriction="restricted"

   See :doc:`How to whitelist an address <whitelist>` For more info on whitelisting

4. Broadcast the transaction to the ethereum network::

    sto --config=myconfig.ini tx-broadcast

5. Make sure the transaction ran sucessfully on the ethereum network::

    sto --config=myconfig.ini tx-update
   See :doc:`broadcast created transactions <broadcast>` for more info.

6. Before distributing token whitelist all the user addresses that will participate in the token distribution.
   To whitelist customer address follow step 2.

7. Distribute the tokens as described in the csv input infile. For more info see :doc:`Distribute Tokens <distribute>` for more info::

    sto --config=myconfig.ini distribute-multiple --csv-input=example-distribution.csv --address=0x....

8. Repeat step 3 and 4.
9. To verify that balances have been set right, view the cap table.::

    sto --config=myconfig.ini cap-table --identity-file=example-ids.csv --token-address=0x..
   See :doc:`View token holder cap table <captable>` for more info.
Further information
-------------------

See :ref:`issue`.
