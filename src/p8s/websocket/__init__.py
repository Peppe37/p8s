"""
P8s WebSocket Support.

Provides Django Channels-style WebSocket support built on Starlette:
- WebSocketEndpoint base class
- Connection management
- JSON/text message handling

Example:
    ```python
    from p8s.websocket import WebSocketEndpoint

    class ChatSocket(WebSocketEndpoint):
        async def on_connect(self, websocket):
            await websocket.accept()
            await websocket.send_text("Welcome!")

        async def on_receive(self, websocket, data):
            await websocket.send_json({"echo": data})

        async def on_disconnect(self, websocket, close_code):
            print(f"Client disconnected: {close_code}")

    # Register route
    app.add_websocket_route("/ws/chat", ChatSocket)
    ```
"""

from typing import Any

from starlette.websockets import WebSocket, WebSocketDisconnect


class WebSocketEndpoint:
    """
    Base class for WebSocket endpoints.

    Subclass this to create your own WebSocket handlers with
    automatic connection lifecycle management.

    The encoding attribute determines how received data is parsed:
    - 'json': Parse as JSON (default)
    - 'text': Raw text string
    - 'bytes': Raw bytes

    Example:
        ```python
        class NotificationSocket(WebSocketEndpoint):
            encoding = "json"

            async def on_connect(self, websocket):
                await websocket.accept()

            async def on_receive(self, websocket, data):
                # data is already parsed as JSON
                await websocket.send_json({"status": "received"})
        ```
    """

    encoding: str = "json"  # 'json', 'text', or 'bytes'

    def __init__(self, scope, receive, send):
        """Initialize with ASGI scope."""
        self.scope = scope
        self.receive = receive
        self.send = send

    async def __call__(self, scope, receive, send):
        """ASGI interface - called for each WebSocket connection."""
        websocket = WebSocket(scope=scope, receive=receive, send=send)

        await self.on_connect(websocket)

        try:
            while True:
                message = await websocket.receive()

                if message["type"] == "websocket.disconnect":
                    close_code = message.get("code", 1000)
                    await self.on_disconnect(websocket, close_code)
                    break

                if message["type"] == "websocket.receive":
                    data = await self._decode_message(message)
                    await self.on_receive(websocket, data)

        except WebSocketDisconnect as e:
            await self.on_disconnect(websocket, e.code)

    async def _decode_message(self, message: dict[str, Any]) -> Any:
        """Decode incoming message based on encoding type."""
        if self.encoding == "json":
            import json

            text = message.get("text", "")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        elif self.encoding == "bytes":
            return message.get("bytes", b"")
        else:
            return message.get("text", "")

    async def on_connect(self, websocket: WebSocket) -> None:
        """
        Called when a WebSocket connection is established.

        Override this to handle connection setup, authentication, etc.
        Don't forget to call `await websocket.accept()` to accept the connection.

        Args:
            websocket: The WebSocket connection
        """
        await websocket.accept()

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        """
        Called when a message is received from the client.

        Override this to handle incoming messages.

        Args:
            websocket: The WebSocket connection
            data: The received data (parsed according to self.encoding)
        """
        pass

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        """
        Called when the WebSocket connection is closed.

        Override this to handle cleanup.

        Args:
            websocket: The WebSocket connection
            close_code: The close code (1000 = normal)
        """
        pass


class ConnectionManager:
    """
    Manages multiple WebSocket connections.

    Useful for broadcasting messages to multiple clients,
    such as in chat applications or real-time notifications.

    Example:
        ```python
        from p8s.websocket import ConnectionManager

        manager = ConnectionManager()

        class ChatSocket(WebSocketEndpoint):
            async def on_connect(self, websocket):
                await websocket.accept()
                await manager.connect(websocket)

            async def on_receive(self, websocket, data):
                await manager.broadcast(data)

            async def on_disconnect(self, websocket, close_code):
                manager.disconnect(websocket)
        ```
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """
        Add a WebSocket to the active connections.

        Args:
            websocket: WebSocket to add
        """
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket from active connections.

        Args:
            websocket: WebSocket to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal(self, message: str, websocket: WebSocket) -> None:
        """
        Send a message to a specific client.

        Args:
            message: Text message to send
            websocket: Target WebSocket
        """
        await websocket.send_text(message)

    async def send_json(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """
        Send JSON to a specific client.

        Args:
            data: Data to send as JSON
            websocket: Target WebSocket
        """
        await websocket.send_json(data)

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a text message to all connected clients.

        Args:
            message: Text message to broadcast
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass  # Connection might be closed

    async def broadcast_json(self, data: dict[str, Any]) -> None:
        """
        Broadcast JSON to all connected clients.

        Args:
            data: Data to broadcast as JSON
        """
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass


# Groups for topic-based broadcasting
class GroupManager:
    """
    Manages WebSocket connections organized into groups/rooms.

    Example:
        ```python
        from p8s.websocket import GroupManager

        groups = GroupManager()

        class RoomSocket(WebSocketEndpoint):
            async def on_connect(self, websocket):
                await websocket.accept()
                room_id = websocket.path_params.get("room_id")
                await groups.add(room_id, websocket)

            async def on_receive(self, websocket, data):
                room_id = websocket.path_params.get("room_id")
                await groups.broadcast(room_id, data["message"])
        ```
    """

    def __init__(self):
        """Initialize group manager."""
        self.groups: dict[str, list[WebSocket]] = {}

    async def add(self, group_name: str, websocket: WebSocket) -> None:
        """
        Add a WebSocket to a group.

        Args:
            group_name: Name of the group
            websocket: WebSocket to add
        """
        if group_name not in self.groups:
            self.groups[group_name] = []
        self.groups[group_name].append(websocket)

    def remove(self, group_name: str, websocket: WebSocket) -> None:
        """
        Remove a WebSocket from a group.

        Args:
            group_name: Name of the group
            websocket: WebSocket to remove
        """
        if group_name in self.groups:
            if websocket in self.groups[group_name]:
                self.groups[group_name].remove(websocket)
            if not self.groups[group_name]:
                del self.groups[group_name]

    async def broadcast(self, group_name: str, message: str) -> None:
        """
        Broadcast a message to all connections in a group.

        Args:
            group_name: Target group
            message: Message to broadcast
        """
        if group_name in self.groups:
            for websocket in self.groups[group_name]:
                try:
                    await websocket.send_text(message)
                except Exception:
                    pass

    async def broadcast_json(self, group_name: str, data: dict[str, Any]) -> None:
        """
        Broadcast JSON to all connections in a group.

        Args:
            group_name: Target group
            data: Data to broadcast
        """
        if group_name in self.groups:
            for websocket in self.groups[group_name]:
                try:
                    await websocket.send_json(data)
                except Exception:
                    pass


__all__ = [
    "WebSocketEndpoint",
    "ConnectionManager",
    "GroupManager",
]
