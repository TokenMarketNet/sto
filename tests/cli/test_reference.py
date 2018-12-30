from sto.cli.main import cli
from sto.generic.reference import generate_reference


def test_generate_command_line_reference():
    generate_reference(cli)