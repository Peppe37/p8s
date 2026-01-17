"""
P8s Commands - Django-style custom management commands.

Provides:
- Base Command class for custom commands
- Automatic command discovery from app directories
- Rich console output

Example:
    # myapp/commands/import_data.py
    from p8s.cli.commands import Command

    class ImportDataCommand(Command):
        name = "import_data"
        help = "Import products from CSV"

        def add_arguments(self, parser):
            parser.add_argument("--file", required=True)

        async def handle(self, **options):
            file_path = options["file"]
            self.stdout.success(f"Imported from {file_path}")

    # Usage:
    # p8s import_data --file=products.csv
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from rich.console import Console


class CommandOutput:
    """Helper for styled command output."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def write(self, message: str) -> None:
        """Write plain message."""
        self.console.print(message)

    def success(self, message: str) -> None:
        """Write success message (green)."""
        self.console.print(f"[green]✓[/green] {message}")

    def warning(self, message: str) -> None:
        """Write warning message (yellow)."""
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        """Write error message (red)."""
        self.console.print(f"[red]✗[/red] {message}")

    def info(self, message: str) -> None:
        """Write info message (blue)."""
        self.console.print(f"[blue]ℹ[/blue] {message}")


class Command(ABC):
    """
    Base class for custom management commands.

    Similar to Django's BaseCommand, provides a standard interface
    for creating CLI commands.

    Example:
        ```python
        from p8s.cli.commands import Command

        class GreetCommand(Command):
            name = "greet"
            help = "Greet a user"

            def add_arguments(self, parser):
                parser.add_argument("--name", default="World")

            async def handle(self, **options):
                name = options["name"]
                self.stdout.success(f"Hello, {name}!")
        ```
    """

    # Command name (used in CLI: p8s <name>)
    name: str = ""

    # Help text shown in --help
    help: str = ""

    def __init__(self) -> None:
        self.stdout = CommandOutput()
        self.stderr = CommandOutput()

    def add_arguments(self, parser: ArgumentParser) -> None:
        """
        Add command-specific arguments.

        Override this method to add arguments to the command.

        Args:
            parser: ArgumentParser instance to add arguments to.
        """
        pass

    @abstractmethod
    async def handle(self, **options: Any) -> None:
        """
        Execute the command.

        Override this method to implement command logic.

        Args:
            **options: Parsed command-line arguments.
        """
        pass

    def execute(self, **options: Any) -> None:
        """Execute the command synchronously."""
        import asyncio

        asyncio.run(self.handle(**options))


def discover_commands(app_paths: list[str] | None = None) -> dict[str, type[Command]]:
    """
    Discover custom commands from app directories.

    Looks for commands in:
    - <app>/commands/*.py
    - <app>/management/commands/*.py (Django-style)

    Args:
        app_paths: List of app module paths to search.

    Returns:
        Dictionary mapping command names to Command classes.
    """
    import importlib
    import pkgutil
    from pathlib import Path

    commands: dict[str, type[Command]] = {}

    if app_paths is None:
        # Try to discover from settings
        try:
            from p8s.core.settings import get_settings

            settings = get_settings()
            app_paths = getattr(settings, "installed_apps", [])
        except Exception:
            app_paths = []

    for app_path in app_paths:
        try:
            # Try to import the app
            app_module = importlib.import_module(app_path)
            app_dir = Path(app_module.__file__).parent if app_module.__file__ else None

            if not app_dir:
                continue

            # Look for commands directory
            commands_dir = app_dir / "commands"
            if commands_dir.exists():
                _discover_from_dir(commands_dir, f"{app_path}.commands", commands)

            # Also check Django-style management/commands
            mgmt_commands_dir = app_dir / "management" / "commands"
            if mgmt_commands_dir.exists():
                _discover_from_dir(
                    mgmt_commands_dir, f"{app_path}.management.commands", commands
                )

        except ImportError:
            continue

    return commands


def _discover_from_dir(
    commands_dir: "Path", module_prefix: str, commands: dict[str, type[Command]]
) -> None:
    """Discover commands from a directory."""
    import importlib
    from pathlib import Path

    for py_file in commands_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        full_module_name = f"{module_prefix}.{module_name}"

        try:
            module = importlib.import_module(full_module_name)

            # Find Command subclasses
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, Command)
                    and attr is not Command
                ):
                    cmd_name = getattr(attr, "name", "") or module_name
                    commands[cmd_name] = attr

        except ImportError:
            continue


# Registry for manually registered commands
_command_registry: dict[str, type[Command]] = {}


def register_command(command_class: type[Command]) -> type[Command]:
    """
    Decorator to register a command class.

    Example:
        ```python
        from p8s.cli.commands import Command, register_command

        @register_command
        class MyCommand(Command):
            name = "mycommand"
            help = "My custom command"

            async def handle(self, **options):
                self.stdout.success("Done!")
        ```
    """
    cmd_name = getattr(command_class, "name", "") or command_class.__name__.lower()
    _command_registry[cmd_name] = command_class
    return command_class


def get_registered_commands() -> dict[str, type[Command]]:
    """Get all registered commands."""
    return _command_registry.copy()


def get_all_commands(app_paths: list[str] | None = None) -> dict[str, type[Command]]:
    """Get all commands (discovered + registered)."""
    commands = discover_commands(app_paths)
    commands.update(_command_registry)
    return commands
