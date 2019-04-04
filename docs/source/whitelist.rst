Restricting share transfers
===========================

Introduction
============

Unlike cryptocurrencies, security tokens have restrictions on transfers.

* The real world identity of a receiver must be resolved before a transfer to maintain up-to-date shareholder registry information

* For limited private companies, restricted shares are often subject to company's approval before they can be given to a new owner

* Bearer shares, or shares without known owner on a shareholder ledger, are illegal in the most jurisdictions

For all of these problems the solution is to "whitelist" token receivers, or shareholders, beforehand.

* A centralised service maintains real world identity information of blockchain addresses offchain

* This centralised service reports to blockchain who are allowed to receive new transfers

Using Know Your Customer smart contract to ensure good ownership
================================================================

Security tokens in the restricted mode need addresses to be whitelisted. Addreses are whitelisted using a KYC
smart contract.

Deploying KYC smart Contract
----------------------------

To deploy the ``KYC`` smart contract::

    sto --config=myconfig.ini kyc-deploy

If the smart contract is already deployed then it wont be re-deployed.

Whitelist an ethereum address
-----------------------------

Adresses can only whitelisted by the owner of the smart contract::

    sto --config=myconfig.ini kyc-manage --whitelist-address='0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF'

The command will also broadcast the transaction to the ethereum network. There is no need to run command ``tx-broadcast``.
