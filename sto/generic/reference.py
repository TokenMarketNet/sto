import re
import textwrap
from click import Group, Context


def remove_ansi(s):
    """https://stackoverflow.com/a/38662876/315168"""
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', s)


def generate_reference(cli: Group):
    with cli.make_context("sto", ["sto"], max_content_width=200, terminal_width=200) as ctx:
        main_help = cli.get_help(ctx)
        main_help = remove_ansi(main_help)
        main_help = textwrap.indent(main_help, "   ")
        print(TEMPLATE.format(main_help))

        for name in sorted(cli.commands.keys()):
            cmd = cli.commands[name]
            with cli.make_context("sto {}".format(name), ["sto", name]) as subcommand_ctx:
                short_help = cmd.help
                long_help = cmd.get_help(subcommand_ctx)
                long_help = textwrap.indent(long_help, "    ")
                print(SUBCOMMAND_TEMPLATE.format(name, name, short_help, long_help))

TEMPLATE = """
Command line reference
======================

Here is the command line reference for ``sto`` command.

.. contents:: :local:

Options and config files
------------------------

Settings can be either given in a config file, specified by ``--config-file`` switch or directly to the main command.

E.g. these are equivalent.

Command line:

.. code-block:: shell

    sto --ethereum-node-url="https://mainnet.infura.io/v3/453d2049c15d4a8da5501a0464fa44f8" token-scan ...
    
As with INI file ``mainnet.ini``:

.. code-block:: ini
    
    # Infura mainnet net node url
    ethereum-node-url = https://mainnet.infura.io/v3/453d2049c15d4a8da5501a0464fa44f8
    
.. code-block:: shell

    sto --config-file=mainnet.ini token-scan ...

Subcommands take their own options that cannot be specified in the settings file.
 
Main command and options
------------------------

When running ``sto --help`` you get list of settings and subcommands:

.. code-block:: text

{}
"""


SUBCOMMAND_TEMPLATE = """

.. _{}:

{}
-------------------------------------

{}

.. code-block:: text

{}

"""