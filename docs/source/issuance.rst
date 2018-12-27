Issuing out security tokens
===========================

Before issuing out stock you need to have set up :doc:`a functional Ethereum account set up <setup>`.

To issue out stock you need to give stock name, ticker symbol and amount of shares::

    sto --config-file=myconfig.ini issue --symbol=STO --name="Mikko's magic corp" --amount=10000

You will get a list of Ethereum transactions needed to perform this operation::

    Prepared transactions for broadcasting for network kovan
    TXID    Status      Nonce  From                                        To                                          Note
    ------  --------  -------  ------------------------------------------  ------------------------------------------  --------------------------------------------------------------
            waiting         1  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Token contract for Mikko's magic corp
            waiting         2  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x1abECD8dF601e6e56eca99Ec1F1c50eEAe61B289  Unrestricted transfer manager for Mikko's magic corp
            waiting         3  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Setting security token transfer manager for Mikko's magic corp
            waiting         4  0xDE5bC059aA433D72F25846bdFfe96434b406FA85  0x3cD6f4004e310c0E5Ae7eaf5B698386ccF1d78F2  Creating 10000 initial shares for Mikko's magic corp

Next see how to :doc:`broadcast created transactions <broadcast>`.