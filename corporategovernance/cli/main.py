"""


"""
import logging
import sys

import configobj
import pkg_resources

import click
import click_config_file
import coloredlogs


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


# Config file docs: https://github.com/phha/click_config_file
@click.group()
@click.option('--config-file', required=False, default="ethereum")
@click.option('--network', required=False, default="ethereum")
@click.option('--ethereum-node-url', required=False, default="http://localhost:8545")
@click.option('--ethereum-contract-abi', required=False)
@click.option('--ethereum-gas-price', required=False)
@click.option('--ethereum-gas-limit', required=False)
@click.option('--ethereum-private-key', required=False)
@click.option('--log-level', default="INFO")
@click.pass_context
def cli(ctx, config_file, **kwargs):
    """Company board activity tool.

    Manage tokenised equity for things like issuing out new, distributing and revoking shares.
    """

    # Fill in arguments from the configuration file
    if config_file:
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
    config.logger = create_command_line_logger(log_level.upper())
    ctx.obj = config

    version = pkg_resources.require("corporategovernance")[0].version
    copyright = "Copyright TokenMarket Ltd. 2018"
    config.logger.info("Corporate governance tool for security tokens, version %s - %s", version, copyright)


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

        private_key = config.ethereum_private_key
        exception = diagnose(config.logger, config.ethereum_node_url, private_key)
        if exception:
            config.logger.error("We identified an issue with your configuration. Please fix the issue above to use this command yet.")
        else:
            config.logger.info("All systems ready to fire")
    else:
        raise UnknownConfiguredNetwork()


@cli.command(name="ethereum-create-account")
@click.pass_obj
def create_ethereum_account(config: BoardCommmadConfiguration):
    """Creates a new Ethereum account and prints out the raw private key."""

    config.logger.info("Creating new Ethereum account.")
    from corporategovernance.ethereum.account import create_account_console
    create_account_console(config.logger)


def main():

    cli()

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