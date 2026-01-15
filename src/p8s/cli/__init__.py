"""
P8s CLI Module - Command line interface.
"""

from p8s.cli.commands import Command, CommandOutput, register_command
from p8s.cli.main import app

__all__ = ["app", "Command", "CommandOutput", "register_command"]
