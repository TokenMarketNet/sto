Developer notes
===============

Information for package developers.

Making a release
----------------

Instructions for the future-maintainers-to-be.

First send out PyPi release:

.. code-block:: shell

    # First edit setup.py manually - auto version bump is broken
    # Build and upload PyPi egg
    export VERSION=0.2.0
    make reference
    make release

Then push out new Docker:

.. code-block:: shell

    # Build docker image
    docker login --username=miohtama
    make publish-docker

Tutorial to add a new command and test if process works end to end
------------------------------------------------------------------

For the purpose of this tutorial, lets create a command ``ethereum-token-transfer`` that takes a private key
and calls ``transfer()``

1. Add the command in ``sto.cli.main``:

.. code-block:: python

    @cli.command(name="ethereum-token-transfer")
    @click.option('--csv-input', required=True, help="CSV file for entities receiving tokens")
    @click.option('--address', required=True, help="Token contract address")
    @click.pass_obj
    def ethereum_token_transfer(config: BoardCommmadConfiguration):
        from sto.distribution import read_csv
        from sto.ethereum.distribution import distribute_tokens

        dists = read_csv(logger, csv_input)
        if not dists:
            sys.exit("Empty CSV file")

        new_txs, old_txs = distribute_tokens(
            logger,
            dbsession,
            config.network,
            ethereum_node_url=config.ethereum_node_url,
            ethereum_abi_file=config.ethereum_abi_file,
            ethereum_private_key=config.ethereum_private_key,
            ethereum_gas_limit=config.ethereum_gas_limit,
            ethereum_gas_price=config.ethereum_gas_price,
            token_address=address,
            dists=dists,
        )
        # write the logic in `distribute_tokens` or refer to `distribute_tokens` method in `sto.ethereum.distribution`

2. Write the necessary fixtures to deploy the smart contracts needed to deploy security token.
   Use the ``deploy`` fixture in ``tests.cli.test_cli``.

.. code-block:: python

    @pytest.fixture
    def kyc_contract(deploy, dbsession, monkeypatch_get_contract_deployed_tx, get_contract_deployed_tx):
        args = {}
        deploy('BasicKYC', args)
        tx = get_contract_deployed_tx(dbsession, 'BasicKYC')
        return tx.contract_address

3. Before issuing tokens whitelist the address that will be used to deploy security token smart contract

.. code-block:: python

    @pytest.fixture
    def whitelisted_owner():
        result = click_runner.invoke(
                cli,
                [
                    '--database-file', db_path,
                    '--ethereum-private-key', private_key_hex,
                    '--ethereum-gas-limit', 999999999,
                    'kyc-manage',
                    '--whitelist-address', priv_key_to_address(private_key_hex)
                ]
            )
            assert result.exit_code == 0

4. Deploy the security token smart contract in restricted mode and broadcast the transaction.

.. code-block:: python

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'issue',
            '--name', "Moo Corp",
            '--symbol', "MOO",
            '--url', "https://tokenmarket.net",
            '--amount', 9999,
            '--transfer-restriction', request.param
        ]
    )

    assert result.exit_code == 0
    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'tx-broadcast',

        ]
    )
    assert result.exit_code == 0

5. Whitelist customer address that will participate in the token distribution.

.. code-block:: python

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            'kyc-manage',
            '--whitelist-address', entry.address
        ]
    )
    assert result.exit_code == 0

6. Distribute the tokens.

.. code-block:: python

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "distribute-multiple",
            '--csv-input', sample_csv_file,
            '--address', token_address
        ]
    )

7. Scan token to update balances

.. code-block:: python

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "token-scan",
            "--token-address", token_address,
        ]
    )

8. Check the cap table

.. code-block:: python

    result = click_runner.invoke(
        cli,
        [
            '--database-file', db_path,
            '--ethereum-private-key', private_key_hex,
            '--ethereum-gas-limit', 999999999,
            "cap-table",
            "--identity-file", csv_file,
            "--token-address", token_address,
        ]
    )
    # parse result.output to check the exact number of entries created as specified in the csv
