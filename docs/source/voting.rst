Voting Contract
===============

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
