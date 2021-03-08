#!/usr/bin/env python

"""Define command line interface and subcommands. """
import logging
import os
import sys

import click
import colorama
import coloredlogs
import configobj
import pkg_resources

from tokfetch.db import setup_database


class UnknownConfiguredNetwork(Exception):
    pass


class BoardCommmadConfiguration:
    """All top level option switcs either read command line or INI

    See ``main.cli()`` arguments for content.
    """

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
    return network in ("ethereum", "kovan", "heco", "hecotest")


INTRO_TEXT = """{}Tokfetch{} token balance fetching tool.

    {}Manage tokenised balances.{}
""".format(colorama.Fore.LIGHTGREEN_EX, colorama.Fore.RESET, colorama.Fore.BLUE, colorama.Fore.RESET)


# --config-file = legacy option name
@click.group(help=INTRO_TEXT)
@click.option('--config', '--config-file', required=False, default=None, help="INI file where to read options from",
              type=click.Path())
@click.option('--database-file', required=False, default="transactions.sqlite", help="SQLite file that persists "
                                                                                     "transaction broadcast status",
              type=click.Path())
@click.option('--network', required=False, default="ethereum",
              help="Network name. Either 'ethereum', 'heco', 'kovan' are supported for now.")
@click.option('--node-url', required=False, default="http://localhost:8545",
              help="Parity or Geth JSON-RPC to connect for Ethereum network access")
@click.option('--log-level', default="INFO", help="Python logging level to tune the verbosity of the command")
@click.pass_context
def cli(ctx, config: str, **kwargs):
    config_file = config

    # Fill in arguments from the configuration file
    if config_file:
        if not os.path.exists(config_file):
            sys.exit("Config file does not exist {}".format(config_file))

        config = configobj.ConfigObj(config_file, raise_errors=True)

        # TODO: Bug here - could not figure out how to pull out from click if an option is set on a command line or
        #  are we using default. Thus you cannot override config file variables by giving a default value from
        #  command line
        for opt in ctx.command.params:  # type: click.core.Options:

            dashed_name = opt.name.replace("_", "-")
            value = kwargs.get(opt.name)
            if value == opt.default:
                config_file_value = config.get(dashed_name)
                if config_file_value:
                    if opt.type == click.types.INT:
                        kwargs[opt.name] = int(config_file_value)
                    else:
                        kwargs[opt.name] = config_file_value

    log_level = kwargs["log_level"]

    config = BoardCommmadConfiguration(**kwargs)
    logger = config.logger = create_command_line_logger(log_level.upper())

    # Mute SQLAlchemy logger who is quite a verbose friend otherwise
    sa_logger = logging.getLogger("sqlalchemy")
    sa_logger.setLevel(logging.WARN)

    prelude = True
    if sys.argv[-1] == "version":
        # Mute generic prelude
        prelude = False

    # Print out the info
    dbfile = os.path.abspath(config.database_file)
    version = pkg_resources.require("tokfetch")[0].version
    config.version = version

    if prelude:
        copyright = "Copyright Illia Likhoshva 2021"
        logger.info("ERC20 (HRC20) token balance fetcher tool, version %s%s%s - %s", colorama.Fore.LIGHTCYAN_EX,
                    version, colorama.Fore.RESET, copyright)
        logger.info("Using database %s%s%s", colorama.Fore.LIGHTCYAN_EX, dbfile, colorama.Fore.RESET)

        config.dbsession, new_db = setup_database(logger, dbfile)
    ctx.obj = config


@cli.command(name="diagnose")
@click.pass_obj
def diagnose(config: BoardCommmadConfiguration):
    """Check your node and account status.

    This command will print out if you are properly connected to Ethereum network and your management account has enough Ether balance.
    """

    # Run Ethereum diagnostics
    if is_ethereum_network(config.network):
        from tokfetch.ethereum.diagnostics import diagnose
        exception = diagnose(config.logger, config.node_url)
        if exception:
            config.logger.error(
                "{}We identified an issue with your configuration. Please fix the issue above to use this command yet.{}".format(
                    colorama.Fore.RED, colorama.Fore.RESET))
        else:
            config.logger.info("{}Ready for action.{}".format(colorama.Fore.LIGHTGREEN_EX, colorama.Fore.RESET))
    else:
        raise UnknownConfiguredNetwork()


@cli.command(name="token-scan")
@click.option('--start-block', required=False, help="The first block where we start (re)scan", type=int, default=None)
@click.option('--end-block', required=False, help="Until which block we scan, also can be 'latest'", type=int,
              default=None)
@click.option('--token-address', required=True, help="Token contract address", default=None)
@click.pass_obj
def token_scan(config: BoardCommmadConfiguration, token_address, start_block, end_block):
    """Update token holder balances from a blockchain to a local database.

    Reads the Ethereum blockchain for a certain token and builds a local database of token holders and transfers.

    If start block and end block information are omitted, continue the scan where we were left last time.
    Scan operations may take a while.
    """

    assert is_ethereum_network(config.network)

    logger = config.logger

    from tokfetch.ethereum.tokenscan import token_scan

    dbsession = config.dbsession
    updated_addresses = token_scan(
        logger,
        dbsession,
        config.network,
        ethereum_node_url=config.node_url,
        token_address=token_address,
        start_block=start_block,
        end_block=end_block
    )

    logger.info("Updated %d token holder balances", len(updated_addresses))


@cli.command(name="richlist")
@click.option('--identity-file', required=False, help="CSV file containing address real world identities", default=None,
              type=click.Path())
@click.option('--token-address', required=True, help="Token contract address", default=None)
@click.option('--order-by', required=False, help="How cap table is sorted", default="balance",
              type=click.Choice(["balance", "name", "updated", "address"]))
@click.option('--order-direction', required=False, help="Sort direction", default="desc",
              type=click.Choice(["asc", "desc"]))
@click.option('--include-empty', required=False, help="Sort direction", default=False, type=bool)
@click.option('--max-entries', required=False, help="Print only first N entries", default=5000, type=int)
@click.option('--accuracy', required=False, help="How many decimals include in balance output", default=2, type=int)
@click.pass_obj
def cap_table(config: BoardCommmadConfiguration, token_address, identity_file, order_by, order_direction, include_empty,
              max_entries, accuracy):
    """Print out token holder cap table.

    The token holder data must have been scanned earlier using token-scan command.

    You can supply optional CSV file that contains Ethereum address mappings to individual token holder names.
    """

    assert is_ethereum_network(config.network)

    logger = config.logger

    from tokfetch.generic.captable import generate_cap_table, print_cap_table
    from tokfetch.identityprovider import read_csv, NullIdentityProvider, CSVIdentityProvider
    from tokfetch.models.implementation import TokenScanStatus, TokenHolderAccount

    dbsession = config.dbsession

    if identity_file:
        entries = read_csv(logger, identity_file)
        provider = CSVIdentityProvider(entries)
    else:
        provider = NullIdentityProvider()

    cap_table = generate_cap_table(logger,
                                   dbsession,
                                   token_address=token_address,
                                   identity_provider=provider,
                                   order_by=order_by,
                                   order_direction=order_direction,
                                   include_empty=include_empty,
                                   TokenScanStatus=TokenScanStatus,
                                   TokenHolderAccount=TokenHolderAccount)

    print_cap_table(cap_table, max_entries, accuracy)


@cli.command(name="reference")
@click.pass_obj
def reference(config: BoardCommmadConfiguration):
    """Print out the command line reference for the documentation."""

    from tokfetch.generic.reference import generate_reference
    generate_reference(cli)


@cli.command(name="version")
@click.pass_obj
def version(config: BoardCommmadConfiguration):
    """Print version number and exit."""
    print(config.version)


def main():
    # https://github.com/pallets/click/issues/204#issuecomment-270012917
    cli.main(max_content_width=200, terminal_width=200)


if __name__ == '__main__':
    main()
