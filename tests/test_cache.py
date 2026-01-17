"""
Tests for the cache system.
"""

import time

import pytest

from p8s.cache.backends import CacheBackend, FileCache, MemoryCache


class TestMemoryCache:
    """Test MemoryCache backend."""

    def test_get_set(self):
        """Test basic get/set operations."""
        cache = MemoryCache()

        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_get_default(self):
        """Test get with default value."""
        cache = MemoryCache()

        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_delete(self):
        """Test delete operation."""
        cache = MemoryCache()

        cache.set("key", "value")
        cache.delete("key")
        assert cache.get("key") is None

    def test_clear(self):
        """Test clear operation."""
        cache = MemoryCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_timeout(self):
        """Test timeout expiration."""
        cache = MemoryCache()

        cache.set("key", "value", timeout=1)
        assert cache.get("key") == "value"

        time.sleep(1.1)
        assert cache.get("key") is None

    def test_has(self):
        """Test has method."""
        cache = MemoryCache()

        assert cache.has("missing") is False
        cache.set("key", "value")
        assert cache.has("key") is True

    def test_get_or_set(self):
        """Test get_or_set method."""
        cache = MemoryCache()

        # Value doesn't exist, should set
        result = cache.get_or_set("key", "default")
        assert result == "default"
        assert cache.get("key") == "default"

        # Value exists, should return existing
        result = cache.get_or_set("key", "new_value")
        assert result == "default"

    def test_get_or_set_callable(self):
        """Test get_or_set with callable default."""
        cache = MemoryCache()

        call_count = [0]

        def expensive():
            call_count[0] += 1
            return "computed"

        result1 = cache.get_or_set("key", expensive)
        result2 = cache.get_or_set("key", expensive)

        assert result1 == "computed"
        assert result2 == "computed"
        assert call_count[0] == 1  # Only called once

    def test_max_entries(self):
        """Test max entries limit."""
        cache = MemoryCache(max_entries=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1

        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_incr(self):
        """Test incr operation."""
        cache = MemoryCache()

        # Create key on first incr
        assert cache.incr("counter") == 1
        assert cache.incr("counter") == 2
        assert cache.incr("counter", 5) == 7

    def test_decr(self):
        """Test decr operation."""
        cache = MemoryCache()

        cache.set("counter", 10)
        assert cache.decr("counter") == 9
        assert cache.decr("counter", 5) == 4

    def test_incr_creates_key(self):
        """Test incr creates key if not exists."""
        cache = MemoryCache()

        assert cache.incr("new_counter", 10) == 10
        assert cache.get("new_counter") == 10

    def test_incr_non_integer_raises(self):
        """Test incr raises ValueError on non-integer."""
        cache = MemoryCache()

        cache.set("string_key", "not_a_number")
        with pytest.raises(ValueError):
            cache.incr("string_key")


class TestFileCache:
    """Test FileCache backend."""

    def test_get_set(self, tmp_path):
        """Test basic get/set operations."""
        cache = FileCache(location=tmp_path / "cache")

        cache.set("key", {"data": "value"})
        assert cache.get("key") == {"data": "value"}

    def test_get_default(self, tmp_path):
        """Test get with default value."""
        cache = FileCache(location=tmp_path / "cache")

        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_delete(self, tmp_path):
        """Test delete operation."""
        cache = FileCache(location=tmp_path / "cache")

        cache.set("key", "value")
        cache.delete("key")
        assert cache.get("key") is None

    def test_clear(self, tmp_path):
        """Test clear operation."""
        cache = FileCache(location=tmp_path / "cache")

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_incr(self, tmp_path):
        """Test incr operation for FileCache."""
        cache = FileCache(location=tmp_path / "cache")

        assert cache.incr("counter") == 1
        assert cache.incr("counter") == 2
        assert cache.incr("counter", 10) == 12

    def test_decr(self, tmp_path):
        """Test decr operation for FileCache."""
        cache = FileCache(location=tmp_path / "cache")

        cache.set("counter", 100)
        assert cache.decr("counter") == 99
        assert cache.decr("counter", 9) == 90


class TestCacheDecorators:
    """Test cache decorators."""

    def test_cache_result(self):
        """Test @cache_result decorator."""
        from p8s.cache import get_cache
        from p8s.cache.decorators import cache_result

        get_cache().clear()
        call_count = [0]

        @cache_result(timeout=300)
        def expensive_func(x):
            call_count[0] += 1
            return x * 2

        result1 = expensive_func(5)
        result2 = expensive_func(5)
        result3 = expensive_func(10)  # Different arg

        assert result1 == 10
        assert result2 == 10
        assert result3 == 20
        assert call_count[0] == 2  # Called twice (once for 5, once for 10)
