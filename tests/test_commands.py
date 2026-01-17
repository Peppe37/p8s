"""
Tests for custom management commands.
"""

from argparse import ArgumentParser

import pytest


class TestCommandClass:
    """Test Command base class."""

    def test_command_import(self):
        """Test Command can be imported."""
        from p8s.cli.commands import Command

        assert Command is not None

    def test_command_output_import(self):
        """Test CommandOutput can be imported."""
        from p8s.cli.commands import CommandOutput

        output = CommandOutput()
        assert output is not None

    def test_command_output_methods(self):
        """Test CommandOutput has expected methods."""
        from p8s.cli.commands import CommandOutput

        output = CommandOutput()
        assert hasattr(output, "write")
        assert hasattr(output, "success")
        assert hasattr(output, "warning")
        assert hasattr(output, "error")
        assert hasattr(output, "info")

    def test_command_name_attribute(self):
        """Test Command has name attribute."""
        from p8s.cli.commands import Command

        class TestCommand(Command):
            name = "test"
            help = "Test command"

            async def handle(self, **options):
                pass

        cmd = TestCommand()
        assert cmd.name == "test"
        assert cmd.help == "Test command"

    def test_command_has_add_arguments(self):
        """Test Command has add_arguments method."""
        from p8s.cli.commands import Command

        class TestCommand(Command):
            name = "test"

            def add_arguments(self, parser):
                parser.add_argument("--name", default="World")

            async def handle(self, **options):
                pass

        cmd = TestCommand()
        parser = ArgumentParser()
        cmd.add_arguments(parser)
        args = parser.parse_args(["--name", "Test"])
        assert args.name == "Test"


class TestCommandRegistry:
    """Test command registration."""

    def test_register_command(self):
        """Test registering a command."""
        from p8s.cli.commands import Command, get_registered_commands, register_command

        @register_command
        class MyTestCommand(Command):
            name = "my_test_cmd"
            help = "My test command"

            async def handle(self, **options):
                pass

        commands = get_registered_commands()
        assert "my_test_cmd" in commands

    def test_get_all_commands(self):
        """Test get_all_commands function."""
        from p8s.cli.commands import get_all_commands

        commands = get_all_commands(app_paths=[])
        assert isinstance(commands, dict)


class TestCommandDiscovery:
    """Test command discovery."""

    def test_discover_commands_returns_dict(self):
        """Test discover_commands returns a dictionary."""
        from p8s.cli.commands import discover_commands

        commands = discover_commands(app_paths=[])
        assert isinstance(commands, dict)

    def test_discover_from_empty_path(self):
        """Test discovery with empty path list."""
        from p8s.cli.commands import discover_commands

        commands = discover_commands(app_paths=[])
        assert commands == {}
