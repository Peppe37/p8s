# WebSocket Support

P8s provides Django Channels-style WebSocket support built on Starlette.

## Quick Start

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

## WebSocketEndpoint

Base class for WebSocket handlers with lifecycle methods:

| Method          | Called When            |
| --------------- | ---------------------- |
| `on_connect`    | Connection established |
| `on_receive`    | Message received       |
| `on_disconnect` | Connection closed      |

### Encoding Options

```python
class MySocket(WebSocketEndpoint):
    encoding = "json"  # "json", "text", or "bytes"
```

## Connection Manager

Manage multiple connections for broadcasting:

```python
from p8s.websocket import ConnectionManager

manager = ConnectionManager()

class NotificationSocket(WebSocketEndpoint):
    async def on_connect(self, websocket):
        await websocket.accept()
        await manager.connect(websocket)

    async def on_receive(self, websocket, data):
        # Broadcast to all connected clients
        await manager.broadcast(data["message"])

    async def on_disconnect(self, websocket, close_code):
        manager.disconnect(websocket)
```

## Group Manager

Organize connections into rooms/groups:

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

    async def on_disconnect(self, websocket, close_code):
        room_id = websocket.path_params.get("room_id")
        groups.remove(room_id, websocket)
```

## Sending Messages

```python
# Text message
await websocket.send_text("Hello")

# JSON message
await websocket.send_json({"type": "notification", "data": {...}})

# Binary message
await websocket.send_bytes(data)
```
