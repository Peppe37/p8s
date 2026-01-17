"""
P8s Command Auto-Discovery - Automatic discovery of custom commands.

Scans project directories for command modules and registers them automatically.

Example structure:
    myapp/
        management/
            commands/
                import_data.py  # Contains ImportDataCommand
                cleanup.py      # Contains CleanupCommand

Usage:
    ```python
    from p8s.cli.discovery import discover_commands, load_commands

    # Discover in current project
    commands = discover_commands("myapp/management/commands")

    # Load and register all commands
    load_commands(cli_app)
    ```
"""

import importlib
import importlib.util
import os
from pathlib import Path
from typing import Any


def discover_commands(
    search_paths: list[str | Path] | None = None,
    pattern: str = "**/*.py",
) -> list[dict[str, Any]]:
    """
    Discover command modules in given paths.

    Args:
        search_paths: Directories to search (defaults to management/commands)
        pattern: Glob pattern for finding command files

    Returns:
        List of discovered command info dicts
    """
    if search_paths is None:
        # Default Django-style paths
        search_paths = [
            Path.cwd() / "management" / "commands",
            Path.cwd() / "commands",
        ]

    discovered = []

    for base_path in search_paths:
        path = Path(base_path)
        if not path.exists():
            continue

        for py_file in path.glob(pattern):
            if py_file.name.startswith("_"):
                continue

            module_name = py_file.stem
            discovered.append(
                {
                    "name": module_name,
                    "path": str(py_file),
                    "module": f"commands.{module_name}",
                }
            )

    return discovered


def load_command_module(file_path: str | Path) -> Any:
    """
    Load a command module from file path.

    Args:
        file_path: Path to Python file

    Returns:
        Loaded module
    """
    path = Path(file_path)
    module_name = f"p8s_cmd_{path.stem}"

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def find_command_class(module: Any) -> type | None:
    """
    Find Command class in a module.

    Looks for class named *Command that has a 'handle' method.

    Args:
        module: Loaded module

    Returns:
        Command class or None
    """
    for name in dir(module):
        if name.startswith("_"):
            continue

        obj = getattr(module, name)
        if not isinstance(obj, type):
            continue

        # Check if it looks like a command class
        if name.endswith("Command") and hasattr(obj, "handle"):
            return obj

    return None


def register_command(
    cli_app: Any,
    command_class: type,
    name: str | None = None,
) -> None:
    """
    Register a command class with the CLI app.

    Args:
        cli_app: Typer or Click app
        command_class: Command class with handle method
        name: Override command name
    """
    import asyncio

    cmd_name = name or getattr(command_class, "name", None)
    if not cmd_name:
        # Convert CommandName to command-name
        class_name = command_class.__name__
        if class_name.endswith("Command"):
            class_name = class_name[:-7]
        cmd_name = _to_kebab_case(class_name)

    help_text = getattr(command_class, "help", command_class.__doc__ or "")

    # Create command instance
    instance = command_class()

    # Create CLI function
    if asyncio.iscoroutinefunction(instance.handle):

        def command_func(**kwargs):
            asyncio.run(instance.handle(**kwargs))
    else:

        def command_func(**kwargs):
            instance.handle(**kwargs)

    command_func.__doc__ = help_text
    command_func.__name__ = cmd_name

    # Register with CLI app
    cli_app.command(name=cmd_name, help=help_text)(command_func)


def _to_kebab_case(name: str) -> str:
    """Convert CamelCase to kebab-case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("-")
        result.append(char.lower())
    return "".join(result)


def load_commands(
    cli_app: Any,
    search_paths: list[str | Path] | None = None,
) -> int:
    """
    Discover and load all commands into CLI app.

    Args:
        cli_app: Typer or Click CLI app
        search_paths: Paths to search for commands

    Returns:
        Number of commands loaded
    """
    discovered = discover_commands(search_paths)
    loaded = 0

    for cmd_info in discovered:
        try:
            module = load_command_module(cmd_info["path"])
            cmd_class = find_command_class(module)

            if cmd_class:
                register_command(cli_app, cmd_class, name=cmd_info["name"])
                loaded += 1
        except Exception as e:
            import logging

            logging.warning(f"Failed to load command {cmd_info['name']}: {e}")

    return loaded


__all__ = [
    "discover_commands",
    "load_command_module",
    "find_command_class",
    "register_command",
    "load_commands",
]
