"""
BioPortal search cache with TTL using SQLite backend.

Provides persistent caching for BioPortal API responses to reduce latency
and API load during metadata authoring sessions. Cache entries expire
based on a configurable TTL (default: 24 hours).
"""

import hashlib
import json
import os
import platform
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Default TTL: 24 hours
DEFAULT_TTL_SECONDS = 86400


def _get_cache_dir() -> Path:
    """
    Get the platform-appropriate cache directory for cedar-mcp.

    Uses the ``CEDAR_MCP_CACHE_DIR`` environment variable if set,
    otherwise falls back to a platform-specific default.

    Returns:
        Path to the cache directory.
    """
    env_override = os.environ.get("CEDAR_MCP_CACHE_DIR")
    if env_override:
        return Path(env_override)

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Caches" / "cedar-mcp"
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            return Path(local_app_data) / "cedar-mcp" / "cache"
        return Path.home() / "AppData" / "Local" / "cedar-mcp" / "cache"
    else:
        # Linux and other POSIX systems
        xdg_cache = os.environ.get("XDG_CACHE_HOME", "")
        if xdg_cache:
            return Path(xdg_cache) / "cedar-mcp"
        return Path.home() / ".cache" / "cedar-mcp"


def _get_ttl() -> int:
    """
    Get the TTL for cache entries in seconds.

    Reads from the ``CEDAR_MCP_CACHE_TTL_SECONDS`` environment variable,
    falling back to 86400 (24 hours).

    Returns:
        TTL in seconds.
    """
    env_val = os.environ.get("CEDAR_MCP_CACHE_TTL_SECONDS")
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            return DEFAULT_TTL_SECONDS
    return DEFAULT_TTL_SECONDS


def _make_cache_key(func_name: str, **params: Any) -> str:
    """
    Create a deterministic cache key from function name and parameters.

    Parameters are sorted by key to ensure identical calls produce the same
    hash regardless of argument order. The API key is excluded from the hash.

    Args:
        func_name: Name of the cached function.
        **params: Function parameters (excluding API keys).

    Returns:
        SHA-256 hex digest string.
    """
    key_data = {"func_name": func_name, "params": dict(sorted(params.items()))}
    key_json = json.dumps(key_data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(key_json.encode("utf-8")).hexdigest()


class BioPortalCache:
    """
    SQLite-backed cache for BioPortal API responses.

    Attributes:
        db_path: Path to the SQLite database file.
        ttl_seconds: Time-to-live for cache entries in seconds.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Initialize the cache, creating the database and table if needed.

        Args:
            db_path: Path to the SQLite database file. Defaults to a
                     platform-appropriate location.
            ttl_seconds: TTL for cache entries. Defaults to the value from
                        ``CEDAR_MCP_CACHE_TTL_SECONDS`` or 86400.
        """
        if db_path is None:
            cache_dir = _get_cache_dir()
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "bioportal_cache.db"
        else:
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else _get_ttl()
        self._init_db()

    def _init_db(self) -> None:
        """Create the cache table if it does not exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    func_name TEXT NOT NULL,
                    params_summary TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    ttl_seconds INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def get(self, func_name: str, **params: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached result if it exists and has not expired.

        On a cache hit, the returned dictionary includes ``_cached: True``
        and ``_cache_age_seconds`` indicating how old the entry is.

        Args:
            func_name: Name of the cached function.
            **params: Function parameters used to build the cache key.

        Returns:
            Cached result dict with metadata on hit, or ``None`` on miss/expiry.
        """
        key = _make_cache_key(func_name, **params)
        now = time.time()

        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT value, created_at, ttl_seconds FROM cache WHERE key = ?",
                (key,),
            ).fetchone()

        if row is None:
            return None

        value_json, created_at, ttl = row
        age = now - created_at
        if age > ttl:
            # Entry expired — remove it
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
            return None

        result: Dict[str, Any] = json.loads(value_json)
        result["_cached"] = True
        result["_cache_age_seconds"] = round(age, 1)
        return result

    def set(self, func_name: str, result: Dict[str, Any], **params: Any) -> None:
        """
        Store a result in the cache.

        Error responses (dicts containing an ``"error"`` key) are **not** cached.

        Args:
            func_name: Name of the cached function.
            result: The API result to cache.
            **params: Function parameters used to build the cache key.
        """
        if "error" in result:
            return

        key = _make_cache_key(func_name, **params)
        value_json = json.dumps(result, ensure_ascii=True)
        params_summary = json.dumps(
            dict(sorted(params.items())), ensure_ascii=True, indent=2
        )

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                    (key, value, func_name, params_summary, created_at, ttl_seconds)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    value_json,
                    func_name,
                    params_summary,
                    time.time(),
                    self.ttl_seconds,
                ),
            )
            conn.commit()

    def remove_stale(self) -> Dict[str, int]:
        """
        Delete all expired cache entries.

        Returns:
            Dictionary with ``removed_count`` and ``remaining_count``.
        """
        now = time.time()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE (? - created_at) > ttl_seconds",
                (now,),
            )
            removed = cursor.rowcount
            conn.commit()
            remaining = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

        return {"removed_count": removed, "remaining_count": remaining}

    def clear_all(self) -> Dict[str, int]:
        """
        Delete all cache entries.

        Returns:
            Dictionary with ``cleared_count``.
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            conn.execute("DELETE FROM cache")
            conn.commit()

        return {"cleared_count": count}
