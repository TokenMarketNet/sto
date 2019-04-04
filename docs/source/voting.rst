======================
Voting by shareholders
======================

Introduction
============

Shareholder voting is a process where equity owners participate in the company wide decisions. We support voting both offchain and onchain.

* In offchain voting, you take a snapshot of registered assembly participants and their voting rights. Then you use a special corporate governance platform to organise voting. An example of such a corporate governance and voting service is `KoreConX <https://koreconx.com>`_.

* In onchain voting, the participants vote on each topic transparently on blockchain, using their token wallets

Using on-chain voting with voting contract
==========================================

This gives shareholders the ability to vote on-chain.

Voting Deploy
-------------
To deploy the voting smart contract run::

    sto --config=myconfig.ini voting-deploy --token-address="0x..." --kyc-address="0x.." --voting-name="abcd" --uri="http://tokenmarket.net" --type="0"

- ``--token-address`` is the address of the deployed security token.
- ``--kyc-address`` is the address of the deployed kyc smart contract.
- ``--voting-name`` is the name you want to give to your Voting smart contract
- ``--uri`` uri used for announcement
- ``--type`` used in announcement smart contract
