======================
Voting by shareholders
======================

Introduction
============

Shareholder voting is a process where equity owners participate in the company wide decisions. We support voting both offchain and onchain.

* In offchain voting, you take a snapshot of registered assembly participants and their voting rights. Then you use a special corporate governance platform to organise voting.

* In onchain voting, the participants vote on each topic transparently on blockchain, using their token wallets

Off-chain voting
================

In off-chain voting, shareholders need to register to present themselves in a general assembly beforehand.

* A snapshot of eligible votes the certain point of time, see :ref:`cap table management <captable>`

* Issuer invites the shareholders to the meeting through email address they have in the :ref:`shareholder registry <whitelist>`

* Issuer opens a master account in the corporate governance system

* Issuer gives registered participants an shareholder account and allocates voting rights proportionally to their registered shares

* The general assembly meeting is run the corporate governance system, each agenda item is voted individually online

* Participants chat with the meeting chair and other participants online in the corporate governance system

* The meetings minutes is automatically produced afterwards

An example of a suitable corporate governance and voting service is `KoreConX <https://koreconx.com>`_.

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
