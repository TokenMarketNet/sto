"""


"""
import logging
import pkg_resources

import click
import click_config_file
import coloredlogs


class UnknownConfiguredNetwork(Exception):
    pass


class BoardCommmadConfiguration:

    def __init__(self, network: str, ethereum_node_url: str, ethereum_contract_abi: dict):
        self.network = network
        self.ethereum_node_url = ethereum_node_url
        self.ethereum_contract_abi = ethereum_contract_abi
        self.logger = None



def create_command_line_logger(log_level):
    """Create a fancy output.

    See: https://coloredlogs.readthedocs.io/en/latest/readme.html#installation
    """
    fmt = "%(message)s"
    logger = logging.getLogger()
    coloredlogs.install(level=log_level, fmt=fmt, logger=logger)
    return logger


# Config file docs: https://github.com/phha/click_config_file
@click.group()
@click.option('--config-file', required=False)
@click.option('--network', required=False, default="ethereum")
@click.option('--ethereum-node-url', required=False)
@click.option('--ethereum-contract-abi', required=False)
@click.option('--log-level', default="INFO")
@click.pass_context
def cli(ctx, config_file, network, ethereum_node_url, ethereum_contract_abi, log_level):
    """Company board activity tool.

    Manage tokenised equity for things like issuing out new, distributing and revoking shares.
    """

    config = BoardCommmadConfiguration(network, ethereum_node_url, ethereum_contract_abi)
    config.logger = create_command_line_logger(log_level.upper())
    ctx.obj = config

    version = pkg_resources.require("corporategovernance")[0].version
    config.logger.info("Corporate governance tool for security tokens, version %s", version)

# click subcommand docs
@cli.command()
@click.option('--symbol', required=True)
@click.option('--name', required=True)
@click.option('--amount', required=True)
def issue(ctx, symbol, name, amount):
    pass


@cli.command()
@click.option('--address', required=True)
def distribute(symbol, name, amount):
    pass


@cli.command()
@click.pass_obj
def diagnose(config: BoardCommmadConfiguration):
    """Show node and account status."""

    # Run Ethereum diagnostics
    if config.network == "ethereum":
        from corporategovernance.ethereum.diagnostics import diagnose
        exception = diagnose(config.logger, config.ethereum_node_url)
        if exception:
            config.logger.error("Diagnostics failure")
        else:
            config.logger.info("All systems green")
    else:
        raise UnknownConfiguredNetwork()


@cli.command()
@click.pass_obj
def create_ethereum_account(config: BoardCommmadConfiguration):
    """Creates a new Ethereum account and prints out the raw private key."""
    pass