"""
Tests for P8s WebSocket support.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestWebSocketEndpoint:
    """Test WebSocketEndpoint base class."""

    def test_websocket_endpoint_import(self):
        """Test WebSocketEndpoint can be imported."""
        from p8s.websocket import WebSocketEndpoint

        assert WebSocketEndpoint is not None

    def test_websocket_endpoint_encoding_default(self):
        """Test default encoding is json."""
        from p8s.websocket import WebSocketEndpoint

        assert WebSocketEndpoint.encoding == "json"

    def test_websocket_endpoint_subclass(self):
        """Test creating a WebSocketEndpoint subclass."""
        from p8s.websocket import WebSocketEndpoint

        class ChatSocket(WebSocketEndpoint):
            encoding = "text"

            async def on_receive(self, websocket, data):
                await websocket.send_text(f"Echo: {data}")

        assert ChatSocket.encoding == "text"


class TestConnectionManager:
    """Test ConnectionManager class."""

    def test_connection_manager_import(self):
        """Test ConnectionManager can be imported."""
        from p8s.websocket import ConnectionManager

        assert ConnectionManager is not None

    def test_connection_manager_init(self):
        """Test ConnectionManager initialization."""
        from p8s.websocket import ConnectionManager

        manager = ConnectionManager()
        assert manager.active_connections == []

    @pytest.mark.asyncio
    async def test_connection_manager_connect(self):
        """Test adding a connection."""
        from p8s.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()

        await manager.connect(mock_ws)

        assert mock_ws in manager.active_connections

    def test_connection_manager_disconnect(self):
        """Test removing a connection."""
        from p8s.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.active_connections.append(mock_ws)

        manager.disconnect(mock_ws)

        assert mock_ws not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_manager_send_personal(self):
        """Test sending personal message."""
        from p8s.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws = AsyncMock()

        await manager.send_personal("Hello", mock_ws)

        mock_ws.send_text.assert_called_once_with("Hello")

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """Test broadcasting to all connections."""
        from p8s.websocket import ConnectionManager

        manager = ConnectionManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        manager.active_connections = [mock_ws1, mock_ws2]

        await manager.broadcast("Hello everyone")

        mock_ws1.send_text.assert_called_once_with("Hello everyone")
        mock_ws2.send_text.assert_called_once_with("Hello everyone")


class TestGroupManager:
    """Test GroupManager for room-based messaging."""

    def test_group_manager_import(self):
        """Test GroupManager can be imported."""
        from p8s.websocket import GroupManager

        assert GroupManager is not None

    def test_group_manager_init(self):
        """Test GroupManager initialization."""
        from p8s.websocket import GroupManager

        groups = GroupManager()
        assert groups.groups == {}

    @pytest.mark.asyncio
    async def test_group_manager_add(self):
        """Test adding connection to group."""
        from p8s.websocket import GroupManager

        groups = GroupManager()
        mock_ws = MagicMock()

        await groups.add("room1", mock_ws)

        assert "room1" in groups.groups
        assert mock_ws in groups.groups["room1"]

    def test_group_manager_remove(self):
        """Test removing connection from group."""
        from p8s.websocket import GroupManager

        groups = GroupManager()
        mock_ws = MagicMock()
        groups.groups["room1"] = [mock_ws]

        groups.remove("room1", mock_ws)

        assert "room1" not in groups.groups

    @pytest.mark.asyncio
    async def test_group_manager_broadcast(self):
        """Test broadcasting to group."""
        from p8s.websocket import GroupManager

        groups = GroupManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        groups.groups["room1"] = [mock_ws1, mock_ws2]

        await groups.broadcast("room1", "Hello room")

        mock_ws1.send_text.assert_called_once_with("Hello room")
        mock_ws2.send_text.assert_called_once_with("Hello room")


class TestWebSocketExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports correct symbols."""
        from p8s.websocket import __all__

        assert "WebSocketEndpoint" in __all__
        assert "ConnectionManager" in __all__
        assert "GroupManager" in __all__
