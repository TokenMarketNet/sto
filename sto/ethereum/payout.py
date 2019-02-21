import decimal

from tqdm import tqdm

from sto.distribution import read_csv
from sto.ethereum.distribution import NotEnoughTokens
from sto.ethereum.txservice import EthereumStoredTXService
from sto.ethereum.utils import create_web3, get_abi
from sto.models.implementation import BroadcastAccount, PreparedTransaction


def payout_investors(
    config,
    csv_input,
    security_token_address,
    payment_type,
    total_amount,
    contract_name,
    token_address
):
    assert payment_type in ['ether', 'token']

    abi = get_abi(config.ethereum_abi_file)
    web3 = create_web3(config.ethereum_node_url)
    service = EthereumStoredTXService(
        config.network,
        config.dbsession,
        web3,
        config.ethereum_private_key,
        config.ethereum_gas_price,
        config.ethereum_gas_limit,
        BroadcastAccount,
        PreparedTransaction
    )
    dists = read_csv(config.logger, csv_input)
    new_distributes = old_distributes = 0

    security_token_total_balance = service.get_total_supply(security_token_address, abi)
    one_unit = decimal.Decimal(total_amount / security_token_total_balance)
    total_to_distribute = sum([dist.amount * one_unit for dist in dists])

    if total_to_distribute > total_amount:
        raise NotEnoughTokens(
            "Total to distribute: {0} exceeds {1}".format(
                total_to_distribute, total_amount
            )
        )

    for d in tqdm(dists):
        if not service.is_distributed(d.external_id, token_address):
            # Going to tx queue
            raw_amount = d.amount * one_unit
            note = "Distributing payout, raw amount: {}".format(raw_amount)
            if payment_type == 'ether':
                service.distribute_ether(d.external_id, d.address, d.amount * one_unit, note)
            else:
                service.distribute_tokens(
                    d.external_id,
                    d.address,
                    d.amount * one_unit,
                    token_address,
                    abi,
                    note,
                    contract_name
                )
                new_distributes += 1
        else:
            # CSV reimports
            old_distributes += 1
