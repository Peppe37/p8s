"""
Tests for P8s Admin Audit Log.
"""

import pytest


class TestActionFlag:
    """Test ActionFlag enum."""

    def test_action_flag_import(self):
        """Test ActionFlag can be imported."""
        from p8s.admin.logs import ActionFlag

        assert ActionFlag.ADDITION == 1
        assert ActionFlag.CHANGE == 2
        assert ActionFlag.DELETION == 3


class TestLogEntry:
    """Test LogEntry model."""

    def test_logentry_import(self):
        """Test LogEntry can be imported."""
        from p8s.admin.logs import LogEntry

        assert LogEntry is not None

    def test_logentry_properties(self):
        """Test LogEntry action properties."""
        from p8s.admin.logs import LogEntry, ActionFlag

        entry = LogEntry(
            content_type="Product",
            object_id="123",
            action_flag=ActionFlag.ADDITION,
        )

        assert entry.is_addition is True
        assert entry.is_change is False
        assert entry.action_name == "Added"


class TestCreateChangeMessage:
    """Test change message creation."""

    def test_create_change_message(self):
        """Test creating change message."""
        from p8s.admin.logs import create_change_message

        changes = {"price": {"old": 10, "new": 15}}
        message = create_change_message(changes)

        assert "price" in message
        assert "10" in message


class TestParseChangeMessage:
    """Test parsing change message."""

    def test_parse_change_message(self):
        """Test parsing change message."""
        from p8s.admin.logs import parse_change_message

        message = '{"price": {"old": 10, "new": 15}}'
        changes = parse_change_message(message)

        assert changes["price"]["old"] == 10

    def test_parse_invalid_returns_empty(self):
        """Test invalid JSON returns empty dict."""
        from p8s.admin.logs import parse_change_message

        changes = parse_change_message("invalid")
        assert changes == {}


class TestCalculateChanges:
    """Test change calculation."""

    def test_calculate_changes(self):
        """Test calculating changes."""
        from p8s.admin.logs import calculate_changes

        old = {"name": "A", "price": 10}
        new = {"name": "A", "price": 15}

        changes = calculate_changes(old, new)

        assert "name" not in changes
        assert changes["price"]["old"] == 10
        assert changes["price"]["new"] == 15


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.admin.logs import __all__

        assert "LogEntry" in __all__
        assert "ActionFlag" in __all__
        assert "log_action" in __all__
