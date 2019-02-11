Address Whitelisting
====================

Security Tokens in the restricted mode need any address to be whitelisted in a KYC smart contrcat.

Deploying KYC smart Contract
----------------------------

To deploy the KYC smart contract::

    sto --config=myconfig.ini kyc-deploy


Whitelist an ethereum address
-----------------------------

Adresses can only whitelisted by the owner of the smart contract::
    sto --config=myconfig.ini kyc-manage --whitelist-address=''