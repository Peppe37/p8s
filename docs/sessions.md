# Session Management

P8s provides Django-style server-side session management.

## Quick Start

```python
from p8s.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware)

# In a route
@app.get("/login/")
async def login(request: Request):
    request.state.session["user_id"] = user.id
    return {"status": "logged_in"}
```

## Configuration

```python
from p8s.sessions import SessionMiddleware, InMemorySessionBackend

app.add_middleware(
    SessionMiddleware,
    backend=InMemorySessionBackend(),
    cookie_name="session_id",
    max_age=86400,  # 24 hours
    secure=True,  # HTTPS only
    httponly=True,  # No JS access
)
```

## Session Backends

### InMemorySessionBackend

For development/testing (data lost on restart):

```python
from p8s.sessions import InMemorySessionBackend

backend = InMemorySessionBackend()
```

### RedisSessionBackend

For production:

```python
from p8s.sessions import RedisSessionBackend

backend = RedisSessionBackend(
    url="redis://localhost:6379",
    prefix="session:",
    default_ttl=86400,
)
```

## Using Sessions

```python
from p8s.sessions import get_session

@app.get("/profile/")
async def profile(request: Request):
    session = get_session(request)

    # Read
    user_id = session.get("user_id")

    # Write
    session["last_visit"] = datetime.now().isoformat()

    # Delete
    del session["temp_data"]

    # Clear
    session.clear()
```

## Session Object

The session behaves like a dictionary and tracks modifications:

```python
session = request.state.session

session["key"] = "value"  # Automatically saved
session.modified  # True if changed
session.is_new  # True if new session
```

## Logging Out

```python
@app.post("/logout/")
async def logout(request: Request):
    session = get_session(request)
    session.clear()
    return {"status": "logged_out"}
```

## Custom Backend

Implement `SessionBackend` for custom storage:

```python
from p8s.sessions import SessionBackend

class DatabaseSessionBackend(SessionBackend):
    async def get(self, session_id):
        # Load from database
        pass

    async def set(self, session_id, data, expires):
        # Save to database
        pass

    async def delete(self, session_id):
        # Delete from database
        pass
```
