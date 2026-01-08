# Caching

Django-style caching with multiple backends and decorators.

## Quick Start

```python
from p8s.cache import cache_get, cache_set, cache_delete

# Set with 5 minute timeout
cache_set("my_key", {"data": "value"}, timeout=300)

# Get
data = cache_get("my_key", default=None)

# Delete
cache_delete("my_key")
```

## Function Caching

```python
from p8s.cache import cache_result

@cache_result(timeout=300)
def expensive_query(user_id: int):
    # This result is cached for 5 minutes
    return db.query(...)

@cache_result(key_prefix="user:", timeout=600)
async def get_user_data(user_id: str):
    ...
```

## Page Caching

```python
from p8s.cache import cache_page

@app.get("/api/stats")
@cache_page(timeout=300)
async def get_stats():
    return {"users": 100}
```

## Backends

### Memory Cache (Default)
```python
from p8s.cache import MemoryCache

cache = MemoryCache(max_entries=1000)
cache.set("key", "value", timeout=60)
```

### File Cache
```python
from p8s.cache import FileCache

cache = FileCache(location=".cache")
cache.set("key", {"data": "value"}, timeout=3600)
```

## Cache Methods

```python
cache.get(key, default=None)     # Get value
cache.set(key, value, timeout)   # Set value
cache.delete(key)                # Delete key
cache.clear()                    # Clear all
cache.has(key)                   # Check exists
cache.get_or_set(key, default, timeout)  # Get or set default
```

## Configuration

In settings.py:
```python
class AppSettings(Settings):
    cache = {
        "backend": "memory",  # or "file", "redis"
        "location": ".cache",
    }
```
