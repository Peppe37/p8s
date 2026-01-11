"""
P8s Cache Decorators - Function and view caching.

Provides:
- cache_result for caching function results
- cache_page for caching API responses
"""

import hashlib
import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


def cache_result(
    timeout: int = 300,
    key_prefix: str = "",
    key_func: Callable[..., str] | None = None,
) -> Callable[[T], T]:
    """
    Decorator to cache function results.

    Example:
        ```python
        from p8s.cache import cache_result

        @cache_result(timeout=3600)
        def expensive_computation(x: int) -> int:
            return x ** 2

        @cache_result(key_prefix="user:", timeout=600)
        async def get_user_data(user_id: str) -> dict:
            ...
        ```

    Args:
        timeout: Cache timeout in seconds (default 300).
        key_prefix: Prefix for cache keys.
        key_func: Custom function to generate cache key from args/kwargs.

    Returns:
        Decorated function.
    """

    def decorator(func: T) -> T:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            from p8s.cache import get_cache

            cache = get_cache()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__] + [str(a) for a in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                raw_key = ":".join(key_parts)
                cache_key = hashlib.md5(raw_key.encode()).hexdigest()

            full_key = f"{key_prefix}{cache_key}"

            # Try to get from cache
            result = cache.get(full_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(full_key, result, timeout)
            return result

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            from p8s.cache import get_cache

            cache = get_cache()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__] + [str(a) for a in args]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                raw_key = ":".join(key_parts)
                cache_key = hashlib.md5(raw_key.encode()).hexdigest()

            full_key = f"{key_prefix}{cache_key}"

            # Try to get from cache
            result = cache.get(full_key)
            if result is not None:
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(full_key, result, timeout)
            return result

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache_page(timeout: int = 600) -> Callable:
    """
    Decorator to cache FastAPI endpoint responses.

    Example:
        ```python
        from p8s.cache import cache_page

        @app.get("/api/stats")
        @cache_page(timeout=300)
        async def get_stats():
            return {"users": 100, "orders": 50}
        ```

    Args:
        timeout: Cache timeout in seconds.

    Returns:
        Decorated endpoint.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            from fastapi import Request

            from p8s.cache import get_cache

            cache = get_cache()

            # Try to get request from args/kwargs for cache key
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            # Generate cache key from request path and query
            if request:
                cache_key = f"page:{request.url.path}:{request.url.query}"
            else:
                cache_key = f"page:{func.__name__}"

            cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            # Try cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call endpoint
            result = await func(*args, **kwargs)

            # Cache JSON-serializable results only
            try:
                json.dumps(result)
                cache.set(cache_key, result, timeout)
            except (TypeError, ValueError):
                pass

            return result

        return wrapper

    return decorator
