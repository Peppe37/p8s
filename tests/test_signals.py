"""
Tests for the signals system.
"""

import pytest

from p8s.db import signals as signals_module
from p8s.db.signals import Signal, connect, disconnect, receiver, send


class TestSignals:
    """Test signal system functionality."""

    def setup_method(self):
        """Clear signal registry before each test."""
        from p8s.db.signals import _signal_handlers

        _signal_handlers.clear()

    def test_connect_and_send(self):
        """Test basic signal connection and sending."""
        received = []

        def handler(sender, **kwargs):
            received.append((sender, kwargs))

        connect(Signal.POST_SAVE, handler)
        send(Signal.POST_SAVE, sender="TestModel", instance="test", created=True)

        assert len(received) == 1
        assert received[0][0] == "TestModel"
        assert received[0][1]["instance"] == "test"
        assert received[0][1]["created"] is True

    def test_connect_with_sender(self):
        """Test signal connection with specific sender."""
        received = []

        def handler(sender, **kwargs):
            received.append(sender)

        connect(Signal.POST_SAVE, handler, sender="Product")

        send(Signal.POST_SAVE, sender="Product", instance="p1")
        send(Signal.POST_SAVE, sender="Order", instance="o1")

        assert len(received) == 1
        assert received[0] == "Product"

    def test_disconnect(self):
        """Test disconnecting a handler."""
        received = []

        def handler(sender, **kwargs):
            received.append(sender)

        connect(Signal.POST_SAVE, handler)
        send(Signal.POST_SAVE, sender="A")

        disconnect(Signal.POST_SAVE, handler)
        send(Signal.POST_SAVE, sender="B")

        assert len(received) == 1
        assert received[0] == "A"

    def test_receiver_decorator(self):
        """Test @receiver decorator."""
        received = []

        @receiver(Signal.POST_SAVE)
        def on_save(sender, **kwargs):
            received.append(sender)

        send(Signal.POST_SAVE, sender="Test")

        assert len(received) == 1
        assert received[0] == "Test"

    def test_receiver_with_sender(self):
        """Test @receiver decorator with sender filter."""
        received = []

        @receiver(Signal.POST_DELETE, sender="User")
        def on_user_delete(sender, **kwargs):
            received.append(sender)

        send(Signal.POST_DELETE, sender="User", instance="u1")
        send(Signal.POST_DELETE, sender="Product", instance="p1")

        assert len(received) == 1


@pytest.mark.asyncio
async def test_send_async():
    """Test async signal sending."""
    from p8s.db.signals import _signal_handlers, send_async

    received = []

    async def async_handler(sender, **kwargs):
        received.append(sender)

    _signal_handlers.clear()
    connect(Signal.POST_SAVE, async_handler)

    await send_async(Signal.POST_SAVE, sender="AsyncTest")

    assert len(received) == 1
    assert received[0] == "AsyncTest"
