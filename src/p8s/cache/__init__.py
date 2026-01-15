"""
P8s Cache - Django-style caching framework.

Provides:
- Multiple cache backends (Memory, Redis, File)
- Cache decorators
- Django-compatible API
"""

from p8s.cache.backends import (
    CacheBackend,
    FileCache,
    MemoryCache,
)
from p8s.cache.decorators import cache_page, cache_result

# Default cache instance
_default_cache: CacheBackend | None = None


def get_cache(backend: str | None = None) -> CacheBackend:
    """
    Get cache backend instance.

    Args:
        backend: Backend type ("memory", "file", "redis") or None for default.

    Returns:
        CacheBackend instance.
    """
    global _default_cache

    if backend is None and _default_cache is not None:
        return _default_cache

    if backend is None:
        try:
            from p8s.core.settings import get_settings

            settings = get_settings()
            cache_settings = getattr(settings, "cache", None)
            if cache_settings:
                backend = getattr(cache_settings, "backend", "memory")
        except Exception:
            backend = "memory"

    backend = backend or "memory"

    if backend == "memory":
        cache = MemoryCache()
    elif backend == "file":
        cache = FileCache()
    elif backend == "redis":
        try:
            from p8s.cache.redis_backend import RedisCache

            cache = RedisCache()
        except ImportError:
            raise ImportError("Redis cache requires 'redis' package: pip install redis")
    else:
        raise ValueError(f"Unknown cache backend: {backend}")

    if _default_cache is None:
        _default_cache = cache

    return cache


# Convenience functions
def cache_get(key: str, default: any = None) -> any:
    """Get value from default cache."""
    return get_cache().get(key, default)


def cache_set(key: str, value: any, timeout: int | None = None) -> None:
    """Set value in default cache."""
    get_cache().set(key, value, timeout)


def cache_delete(key: str) -> None:
    """Delete key from default cache."""
    get_cache().delete(key)


def cache_clear() -> None:
    """Clear all keys from default cache."""
    get_cache().clear()


__all__ = [
    # Backends
    "CacheBackend",
    "MemoryCache",
    "FileCache",
    # Functions
    "get_cache",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear",
    # Decorators
    "cache_page",
    "cache_result",
    "cache",  # Alias for cache_result
]

# Alias for intuitive import: from p8s.cache import cache
cache = cache_result
