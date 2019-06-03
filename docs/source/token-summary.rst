Token summary
=============

Introduction
------------

Token summary commands allow you to check the overview of existing deployed STO smart contracts.

Viewing summary
---------------

After all your transactions have been pushed out and are succesfully included in blocks, you can view the token status by entering the contract address::

    sto --config=myconfig.ini token-status --address=0xa2016C64D4687Ad4184bA1dA98711e83a36eD1c2

This outputs::

    Name: Boobar
    Symbol: STO
    Total supply: 10000
    Decimals: 18
    Owner: 0xDE5bC059aA433D72F25846bdFfe96434b406FA85
    Transfer verified: 0x7598E970888F51d7D35468E50768Fa5F21B46Bb3