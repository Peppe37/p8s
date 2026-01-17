"""
Tests for P8s CLI Check.
"""

import pytest


class TestCheckLevel:
    """Test CheckLevel enum."""

    def test_check_level_import(self):
        """Test CheckLevel can be imported."""
        from p8s.cli.check import CheckLevel

        assert CheckLevel.ERROR.value == "error"
        assert CheckLevel.WARNING.value == "warning"


class TestCheckMessage:
    """Test CheckMessage dataclass."""

    def test_check_message_import(self):
        """Test CheckMessage can be imported."""
        from p8s.cli.check import CheckMessage, CheckLevel

        msg = CheckMessage(
            level=CheckLevel.ERROR,
            message="Test error",
            hint="Fix it",
        )

        assert msg.is_error is True
        assert msg.is_warning is False

    def test_warning_message(self):
        """Test warning classification."""
        from p8s.cli.check import CheckMessage, CheckLevel

        msg = CheckMessage(
            level=CheckLevel.WARNING,
            message="Test warning",
        )

        assert msg.is_error is False
        assert msg.is_warning is True


class TestRegisterCheck:
    """Test check registration."""

    def test_register_check_import(self):
        """Test register_check can be imported."""
        from p8s.cli.check import register_check

        assert register_check is not None

    def test_register_and_get_checks(self):
        """Test registering and getting checks."""
        from p8s.cli.check import register_check, get_checks

        @register_check("test")
        def test_check():
            return []

        checks = get_checks(["test"])
        assert len(checks) >= 1


class TestRunChecks:
    """Test running checks."""

    def test_run_checks_import(self):
        """Test run_checks can be imported."""
        from p8s.cli.check import run_checks

        assert run_checks is not None

    @pytest.mark.asyncio
    async def test_run_all_checks(self):
        """Test running all checks."""
        from p8s.cli.check import run_checks

        messages = await run_checks()
        assert isinstance(messages, list)


class TestFormatResults:
    """Test result formatting."""

    def test_format_no_issues(self):
        """Test formatting empty results."""
        from p8s.cli.check import format_check_results

        result = format_check_results([])
        assert "no issues" in result

    def test_format_with_errors(self):
        """Test formatting with errors."""
        from p8s.cli.check import format_check_results, CheckMessage, CheckLevel

        messages = [
            CheckMessage(level=CheckLevel.ERROR, message="Error 1"),
            CheckMessage(level=CheckLevel.WARNING, message="Warning 1"),
        ]

        result = format_check_results(messages)
        assert "ERRORS" in result
        assert "WARNINGS" in result


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.cli.check import __all__

        assert "CheckLevel" in __all__
        assert "CheckMessage" in __all__
        assert "run_checks" in __all__
