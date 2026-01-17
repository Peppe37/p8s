"""
Tests for P8s CLI Discovery.
"""

import pytest
from pathlib import Path
import tempfile


class TestDiscoverCommands:
    """Test command discovery."""

    def test_discover_commands_import(self):
        """Test discover_commands can be imported."""
        from p8s.cli.discovery import discover_commands

        assert discover_commands is not None

    def test_discover_empty_paths(self):
        """Test discovering from non-existent paths."""
        from p8s.cli.discovery import discover_commands

        result = discover_commands(["/nonexistent/path"])
        assert result == []


class TestLoadCommandModule:
    """Test loading command modules."""

    def test_load_command_module_import(self):
        """Test function can be imported."""
        from p8s.cli.discovery import load_command_module

        assert load_command_module is not None

    def test_load_valid_module(self):
        """Test loading a valid Python file."""
        from p8s.cli.discovery import load_command_module

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("class TestCommand:\n    def handle(self): pass\n")
            f.flush()

            module = load_command_module(f.name)
            assert hasattr(module, "TestCommand")


class TestFindCommandClass:
    """Test finding command classes."""

    def test_find_command_class_import(self):
        """Test function can be imported."""
        from p8s.cli.discovery import find_command_class

        assert find_command_class is not None

    def test_find_class_with_handle(self):
        """Test finding class with handle method."""
        from p8s.cli.discovery import find_command_class, load_command_module

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("class ImportCommand:\n    def handle(self): pass\n")
            f.flush()

            module = load_command_module(f.name)
            cmd_class = find_command_class(module)

            assert cmd_class is not None
            assert cmd_class.__name__ == "ImportCommand"


class TestToKebabCase:
    """Test kebab-case conversion."""

    def test_kebab_case(self):
        """Test CamelCase to kebab-case."""
        from p8s.cli.discovery import _to_kebab_case

        assert _to_kebab_case("ImportData") == "import-data"
        assert _to_kebab_case("Test") == "test"
        assert _to_kebab_case("MyLongCommand") == "my-long-command"


class TestLoadCommands:
    """Test loading all commands."""

    def test_load_commands_import(self):
        """Test function can be imported."""
        from p8s.cli.discovery import load_commands

        assert load_commands is not None


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.cli.discovery import __all__

        assert "discover_commands" in __all__
        assert "load_commands" in __all__
        assert "find_command_class" in __all__
