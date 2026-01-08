"""
P8s Cache Backends - Configurable cache storage backends.

Provides:
- MemoryCache for in-process caching
- FileCache for persistent file-based caching
"""

import json
import hashlib
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import threading


class CacheBackend(ABC):
    """
    Abstract base class for cache backends.
    """
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        """Set value in cache with optional timeout (seconds)."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all keys from cache."""
        pass
    
    def get_or_set(self, key: str, default: Any, timeout: int | None = None) -> Any:
        """Get value or set default if not exists."""
        value = self.get(key)
        if value is None:
            if callable(default):
                value = default()
            else:
                value = default
            self.set(key, value, timeout)
        return value
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None


class MemoryCache(CacheBackend):
    """
    In-memory cache backend.
    
    Fast but not shared between processes.
    
    Example:
        ```python
        cache = MemoryCache()
        cache.set("key", "value", timeout=300)
        print(cache.get("key"))  # "value"
        ```
    """
    
    def __init__(self, max_entries: int = 1000) -> None:
        """
        Initialize memory cache.
        
        Args:
            max_entries: Maximum number of cache entries (LRU eviction).
        """
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._max_entries = max_entries
        self._lock = threading.Lock()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return default
            
            value, expires_at = self._cache[key]
            
            # Check expiration
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return default
            
            return value
    
    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self._max_entries and key not in self._cache:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            
            expires_at = time.time() + timeout if timeout else None
            self._cache[key] = (value, expires_at)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        with self._lock:
            now = time.time()
            expired = [
                k for k, (_, exp) in self._cache.items()
                if exp is not None and now > exp
            ]
            for k in expired:
                del self._cache[k]
            return len(expired)


class FileCache(CacheBackend):
    """
    File-based cache backend.
    
    Persists cache entries to disk, shared between processes.
    
    Example:
        ```python
        cache = FileCache(location="/tmp/cache")
        cache.set("key", {"data": "value"}, timeout=3600)
        ```
    """
    
    def __init__(self, location: str | Path = ".cache") -> None:
        """
        Initialize file cache.
        
        Args:
            location: Directory for cache files.
        """
        self.location = Path(location)
        self.location.mkdir(parents=True, exist_ok=True)
    
    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path."""
        # Hash the key to get a safe filename
        hashed = hashlib.sha256(key.encode()).hexdigest()
        return self.location / f"{hashed}.cache"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        path = self._key_to_path(key)
        
        if not path.exists():
            return default
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            expires_at = data.get("expires_at")
            if expires_at is not None and time.time() > expires_at:
                path.unlink(missing_ok=True)
                return default
            
            return data.get("value", default)
        except Exception:
            return default
    
    def set(self, key: str, value: Any, timeout: int | None = None) -> None:
        """Set value in cache."""
        path = self._key_to_path(key)
        
        data = {
            "value": value,
            "expires_at": time.time() + timeout if timeout else None,
            "created_at": time.time(),
        }
        
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except Exception:
            pass
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        path = self._key_to_path(key)
        path.unlink(missing_ok=True)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        for path in self.location.glob("*.cache"):
            try:
                path.unlink()
            except Exception:
                pass
