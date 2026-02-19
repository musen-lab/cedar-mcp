"""Unit tests for the BioPortal search cache module."""

import time
from pathlib import Path

import pytest

from cedar_mcp.cache import BioPortalCache, _get_cache_dir, _make_cache_key


@pytest.mark.unit
class TestMakeCacheKey:
    """Tests for the _make_cache_key helper."""

    def test_returns_hex_string(self) -> None:
        """Cache key should be a hex-encoded SHA-256 digest."""
        key = _make_cache_key("func", a="1")
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_deterministic(self) -> None:
        """Same inputs should always produce the same key."""
        k1 = _make_cache_key("search", q="aspirin", onto="CHEBI")
        k2 = _make_cache_key("search", q="aspirin", onto="CHEBI")
        assert k1 == k2

    def test_param_order_irrelevant(self) -> None:
        """Parameter order should not affect the cache key."""
        k1 = _make_cache_key("search", a="1", b="2")
        k2 = _make_cache_key("search", b="2", a="1")
        assert k1 == k2

    def test_different_params_produce_different_keys(self) -> None:
        """Different parameter values should produce different keys."""
        k1 = _make_cache_key("search", q="aspirin")
        k2 = _make_cache_key("search", q="glucose")
        assert k1 != k2

    def test_different_func_names_produce_different_keys(self) -> None:
        """Different function names should produce different keys."""
        k1 = _make_cache_key("func_a", q="aspirin")
        k2 = _make_cache_key("func_b", q="aspirin")
        assert k1 != k2


@pytest.mark.unit
class TestGetCacheDir:
    """Tests for _get_cache_dir."""

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """CEDAR_MCP_CACHE_DIR should override the default location."""
        custom_dir = tmp_path / "custom_cache"
        monkeypatch.setenv("CEDAR_MCP_CACHE_DIR", str(custom_dir))
        assert _get_cache_dir() == custom_dir


@pytest.mark.unit
class TestBioPortalCache:
    """Tests for the BioPortalCache class."""

    def test_miss_returns_none(self, tmp_cache: BioPortalCache) -> None:
        """A cache miss should return None."""
        result = tmp_cache.get("search", q="nonexistent")
        assert result is None

    def test_set_get_roundtrip(self, tmp_cache: BioPortalCache) -> None:
        """Stored values should be retrievable."""
        data = {"collection": [{"prefLabel": "Aspirin"}]}
        tmp_cache.set("search", data, q="aspirin", onto="CHEBI")

        cached = tmp_cache.get("search", q="aspirin", onto="CHEBI")
        assert cached is not None
        assert cached["collection"] == [{"prefLabel": "Aspirin"}]
        assert cached["_cached"] is True
        assert "_cache_age_seconds" in cached

    def test_error_responses_not_cached(self, tmp_cache: BioPortalCache) -> None:
        """Results containing an 'error' key should not be stored."""
        tmp_cache.set("search", {"error": "API failed"}, q="aspirin")
        assert tmp_cache.get("search", q="aspirin") is None

    def test_ttl_expiration(self, tmp_path: Path) -> None:
        """Expired entries should return None on get."""
        cache = BioPortalCache(db_path=tmp_path / "ttl.db", ttl_seconds=1)
        cache.set("search", {"data": "ok"}, q="aspirin")

        # Should be available immediately
        assert cache.get("search", q="aspirin") is not None

        # Wait for expiry
        time.sleep(1.1)
        assert cache.get("search", q="aspirin") is None

    def test_remove_stale_deletes_expired(self, tmp_path: Path) -> None:
        """remove_stale should delete only expired entries."""
        cache = BioPortalCache(db_path=tmp_path / "stale.db", ttl_seconds=1)
        cache.set("search", {"data": "old"}, q="old_query")

        time.sleep(1.1)

        # Add a fresh entry
        cache.set("search", {"data": "new"}, q="new_query")

        result = cache.remove_stale()
        assert result["removed_count"] == 1
        assert result["remaining_count"] == 1

        # Fresh entry should still be there
        assert cache.get("search", q="new_query") is not None

    def test_clear_all(self, tmp_cache: BioPortalCache) -> None:
        """clear_all should remove all entries and return the count."""
        tmp_cache.set("search", {"data": "1"}, q="a")
        tmp_cache.set("search", {"data": "2"}, q="b")
        tmp_cache.set("search", {"data": "3"}, q="c")

        result = tmp_cache.clear_all()
        assert result["cleared_count"] == 3

        assert tmp_cache.get("search", q="a") is None
        assert tmp_cache.get("search", q="b") is None

    def test_cache_survives_reconnection(self, tmp_path: Path) -> None:
        """A new BioPortalCache instance should read existing data."""
        db_path = tmp_path / "persist.db"
        cache1 = BioPortalCache(db_path=db_path, ttl_seconds=3600)
        cache1.set("search", {"data": "persistent"}, q="aspirin")

        # Create a new instance with the same db_path
        cache2 = BioPortalCache(db_path=db_path, ttl_seconds=3600)
        cached = cache2.get("search", q="aspirin")
        assert cached is not None
        assert cached["data"] == "persistent"

    def test_cache_age_increases(self, tmp_cache: BioPortalCache) -> None:
        """_cache_age_seconds should reflect real elapsed time."""
        tmp_cache.set("search", {"data": "timed"}, q="aspirin")
        time.sleep(0.5)
        cached = tmp_cache.get("search", q="aspirin")
        assert cached is not None
        assert cached["_cache_age_seconds"] >= 0.4
