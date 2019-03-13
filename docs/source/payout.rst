Payout Contract
===============

The Payout contract provides the ability to set up dividend distribution.

Payout Deploy
-------------

To deploy payout smart contract::

    sto --config=myconfig.ini payout-deploy --token-address="0x.." --payout-token-address="0x.." --payout-token-name="CrowdsaleToken" --kyc-address="0x.." --payout-name='Pay X' --uri="http://tokenmarket.net" --type=0

- ``--token-address`` is the address of the deployed security token.
- ``--payout-token-address`` is the address token used in paying out.
- ``--payout-token-name`` is the name of the payout token. This should be the same name as defined in the smart contract.
- ``--kyc-address`` is the address of the deployed kyc smart contract.
- ``--payout-name`` is the name you want to give to your Payout smart contract
- ``--uri`` uri used for announcement
- ``--type`` used in announcement smart contract

Payout Approve
--------------

In order to release token to the Payout smart contract, they first need to be approved. This should only be run once::

    sto --config=myconfig.ini payout-approve --payout-token-name="CrowdsaleToken"


``--payout-token-name`` name of the payout_token used earlier to deploy payout smart contract.


Payout deposit
--------------

To fetch the approved tokens call command::

    sto --config=myconfig.ini payout-deposit
