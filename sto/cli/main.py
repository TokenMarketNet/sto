"""


"""
import logging
import os
import sys

import colorama
import configobj
import pkg_resources

import click
import coloredlogs
from sto.db import setup_database


class UnknownConfiguredNetwork(Exception):
    pass


class BoardCommmadConfiguration:

    def __init__(self, **kwargs):
        # See cli() for descriptions of variables
        self.__dict__.update(kwargs)


def create_command_line_logger(log_level):
    """Create a fancy output.

    See: https://coloredlogs.readthedocs.io/en/latest/readme.html#installation
    """
    fmt = "%(message)s"
    logger = logging.getLogger()
    coloredlogs.install(level=log_level, fmt=fmt, logger=logger)
    return logger


def is_ethereum_network(network: str):
    return network in ("ethereum", "kovan", "ropsten")



INTRO_TEXT = """{}TokenMarket{} security token management tool.

    {}Manage tokenised equity for things like issuing out new, distributing and revoking shares.{}
""".format(colorama.Fore.LIGHTGREEN_EX, colorama.Fore.RESET, colorama.Fore.BLUE, colorama.Fore.RESET)



@click.group(help=INTRO_TEXT)
@click.option('--config-file', required=False, default=None, help="INI file where to read options from", type=click.Path())
@click.option('--database-file', required=False, default="transactions.sqlite", help="SQLite file that persists transaction broadcast status", type=click.Path())
@click.option('--network', required=False, default="ethereum", help="Network name. Either 'ethereum' or 'kovan' are supported for now.")
@click.option('--ethereum-node-url', required=False, default="http://localhost:8545", help="Parity or Geth JSON-RPC to connect for Ethereum network access")
@click.option('--ethereum-abi-file', required=False, help='Solidity compiler output JSON to override default smart contracts')
@click.option('--ethereum-gas-price', required=False, help='How many GWei we pay for gas')
@click.option('--ethereum-gas-limit', required=False, help='What is the transaction gas limit for broadcasts', type=int)
@click.option('--ethereum-private-key', required=False, help='Private key for the broadcasting account')
@click.option('--log-level', default="INFO", help="Python logging level to tune the verbosity of the command")
@click.pass_context
def cli(ctx, config_file, **kwargs):

    # Fill in arguments from the configuration file
    if config_file:
        if not os.path.exists(config_file):

            sys.exit("Config file does not exist {}".format(config_file))

        config = configobj.ConfigObj(config_file, raise_errors=True)

        # TODO: Bug here - could not figure out how to pull out from click if an option is set on a command line or are we using default.
        # Thus you cannot override config file variables by giving a default value from command line
        for opt in ctx.command.params:  # type: click.core.Options:

            dashed_name = opt.name.replace("_", "-")
            value = kwargs.get(opt.name)
            if value == opt.default:
                config_file_value = config.get(dashed_name)
                if config_file_value:
                    kwargs[opt.name] = config_file_value  # TODO: opt.process_value

    log_level = kwargs["log_level"]

    config = BoardCommmadConfiguration(**kwargs)
    logger = config.logger = create_command_line_logger(log_level.upper())

    # Mute SQLAlchemy logger who is quite a verbose friend otherwise
    sa_logger = logging.getLogger("sqlalchemy")
    sa_logger.setLevel(logging.WARN)

    dbfile = os.path.abspath(config.database_file)
    config.dbsession = setup_database(logger, dbfile)
    ctx.obj = config

    version = pkg_resources.require("sto")[0].version
    copyright = "Copyright TokenMarket Ltd. 2018"
    logger.info("STO tool, version %s - %s", version, copyright)
    logger.info("Using database %s", dbfile)


@cli.command()
@click.option('--symbol', required=True)
@click.option('--name', required=True)
@click.option('--amount', required=True, type=int)
@click.option('--transfer-restriction', required=False, default="unrestricted")
@click.pass_obj
def issue(config: BoardCommmadConfiguration, symbol, name, amount, transfer_restriction):
    """Issue out a new security token."""

    logger = config.logger

    assert is_ethereum_network(config.network) # Nothing else implemented yet

    from sto.ethereum.issuance import deploy_token_contracts
    from sto.ethereum.txservice import EthereumStoredTXService

    dbsession = config.dbsession

    txs = deploy_token_contracts(logger,
                          dbsession,
                          config.network,
                          ethereum_node_url=config.ethereum_node_url,
                          ethereum_abi_file=config.ethereum_abi_file,
                          ethereum_private_key=config.ethereum_private_key,
                          ethereum_gas_limit=config.ethereum_gas_limit,
                          ethereum_gas_price=config.ethereum_gas_price,
                          name=name,
                          symbol=symbol,
                          amount=amount,
                          transfer_restriction=transfer_restriction)

    EthereumStoredTXService.print_transactions(txs)

    # Write database
    dbsession.commit()

    logger.info("Run %ssto tx-broadcast%s to write this to blockchain", colorama.Fore.LIGHTCYAN_EX, colorama.Fore.RESET)


@cli.command(name="token-status")
@click.option('--address', required=True, help="Token contract addrss")
@click.pass_obj
def status(config: BoardCommmadConfiguration, address):
    """Print token contract status."""

    logger = config.logger

    assert is_ethereum_network(config.network) # Nothing else implemented yet

    from sto.ethereum.issuance import contract_status

    dbsession = config.dbsession

    contract_status(logger,
      dbsession,
      config.network,
      ethereum_node_url=config.ethereum_node_url,
      ethereum_abi_file=config.ethereum_abi_file,
      ethereum_private_key=config.ethereum_private_key,
      ethereum_gas_limit=config.ethereum_gas_limit,
      ethereum_gas_price=config.ethereum_gas_price,
      token_contract=address)


@cli.command()
@click.option('--csv-input', required=True, help="CSV file for entities receiving tokens")
@click.pass_obj
def distribute(config: BoardCommmadConfiguration, csv_input):
    """Distribute shares to shareholders."""

    logger = config.logger

    assert is_ethereum_network(config.network) # Nothing else implemented yet
    dbsession = config.dbsession

    from sto.distribution import read_csv

    dists = read_csv(logger, csv_input)
    if not dists:
        sys.exit("Empty CSV file")

    txs =

    # Write database
    dbsession.commit()

    logger.info("Run %ssto tx-broadcast%s to send out issued shares to the world", colorama.Fore.LIGHTCYAN_EX, colorama.Fore.RESET)



@cli.command()
@click.pass_obj
def diagnose(config: BoardCommmadConfiguration):
    """Show your node and account status."""

    # Run Ethereum diagnostics
    if is_ethereum_network(config.network):
        from sto.ethereum.diagnostics import diagnose

        private_key = config.ethereum_private_key
        exception = diagnose(config.logger, config.ethereum_node_url, private_key)
        if exception:
            config.logger.error("{}We identified an issue with your configuration. Please fix the issue above to use this command yet.{}".format(colorama.Fore.RED, colorama.Fore.RESET))
        else:
            config.logger.info("{}Ready for action.{}".format(colorama.Fore.LIGHTGREEN_EX, colorama.Fore.RESET))
    else:
        raise UnknownConfiguredNetwork()


@cli.command(name="ethereum-create-account")
@click.pass_obj
def create_ethereum_account(config: BoardCommmadConfiguration):
    """Creates a new Ethereum account."""

    config.logger.info("Creating new Ethereum account.")
    from sto.ethereum.account import create_account_console
    create_account_console(config.logger, config.network)


@cli.command(name="tx-broadcast")
@click.pass_obj
def broadcast(config: BoardCommmadConfiguration):
    """Broadcast waiting transactions."""

    assert is_ethereum_network(config.network)

    logger = config.logger

    from sto.ethereum.broadcast import broadcast

    dbsession = config.dbsession

    txs = broadcast(logger,
                          dbsession,
                          config.network,
                          ethereum_node_url=config.ethereum_node_url,
                          ethereum_private_key=config.ethereum_private_key,
                          ethereum_gas_limit=config.ethereum_gas_limit,
                          ethereum_gas_price=config.ethereum_gas_price)

    if txs:
        from sto.ethereum.txservice import EthereumStoredTXService
        EthereumStoredTXService.print_transactions(txs)
        logger.info("Run %ssto tx-update%s to monitor your transaction propagation status", colorama.Fore.LIGHTCYAN_EX, colorama.Fore.RESET)

    # Write database
    dbsession.commit()


@cli.command(name="tx-update")
@click.pass_obj
def update(config: BoardCommmadConfiguration):
    """Update transaction status."""

    assert is_ethereum_network(config.network)

    logger = config.logger

    from sto.ethereum.status import update_status

    dbsession = config.dbsession

    txs = update_status(logger,
                          dbsession,
                          config.network,
                          ethereum_node_url=config.ethereum_node_url,
                          ethereum_private_key=config.ethereum_private_key,
                          ethereum_gas_limit=config.ethereum_gas_limit,
                          ethereum_gas_price=config.ethereum_gas_price)

    if txs:
        from sto.ethereum.txservice import EthereumStoredTXService
        EthereumStoredTXService.print_transactions(txs)

    # Write database
    dbsession.commit()


@cli.command(name="tx-last")
@click.option('--limit', required=False, help="How many transcations to print", default=5)
@click.pass_obj
def last(config: BoardCommmadConfiguration, limit):
    """Print latest transctions from database."""

    assert is_ethereum_network(config.network)

    logger = config.logger

    from sto.ethereum.last import get_last_transactions

    dbsession = config.dbsession

    txs = get_last_transactions(logger,
                          dbsession,
                          config.network,
                          limit=limit,
                          ethereum_node_url=config.ethereum_node_url,
                          ethereum_private_key=config.ethereum_private_key,
                          ethereum_gas_limit=config.ethereum_gas_limit,
                          ethereum_gas_price=config.ethereum_gas_price)

    if txs:
        from sto.ethereum.txservice import EthereumStoredTXService
        EthereumStoredTXService.print_transactions(txs)


@cli.command(name="tx-restart-nonce")
@click.pass_obj
def restart_nonce(config: BoardCommmadConfiguration):
    """Resets the broadcasting account nonce."""

    assert is_ethereum_network(config.network)

    logger = config.logger

    from sto.ethereum.nonce import restart_nonce

    dbsession = config.dbsession

    txs = restart_nonce(logger,
                          dbsession,
                          config.network,
                          ethereum_node_url=config.ethereum_node_url,
                          ethereum_private_key=config.ethereum_private_key,
                          ethereum_gas_limit=config.ethereum_gas_limit,
                          ethereum_gas_price=config.ethereum_gas_price)

@cli.command(name="tx-next-nonce")
@click.pass_obj
def next_nonce(config: BoardCommmadConfiguration):
    """Print next nonce to be consumed."""

    assert is_ethereum_network(config.network)

    logger = config.logger

    from sto.ethereum.nonce import next_nonce

    dbsession = config.dbsession

    txs = next_nonce(logger,
                          dbsession,
                          config.network,
                          ethereum_node_url=config.ethereum_node_url,
                          ethereum_private_key=config.ethereum_private_key,
                          ethereum_gas_limit=config.ethereum_gas_limit,
                          ethereum_gas_price=config.ethereum_gas_price)



def main():
    # https://github.com/pallets/click/issues/204#issuecomment-270012917
    cli.main(max_content_width=200, terminal_width=200)

    # import cProfile
    # pr = cProfile.Profile()
    # try:
    #     pr.runcall(cli)
    # except:
    #     pass
    #
    # import pstats
    # stats =  pstats.Stats(pr)
    # stats.sort_stats('cumulative').print_stats(50)