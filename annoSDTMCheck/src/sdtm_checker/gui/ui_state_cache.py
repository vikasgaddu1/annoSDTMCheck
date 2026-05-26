"""
UI state caching system for SDTM Annotation Checker.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class UIStateCache:
    """Manages caching of UI state to improve performance."""

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize the UI state cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "ui_state.json"
        self._state: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cached state from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self._state = json.load(f)
                logger.info("Loaded UI state from cache")
        except Exception as e:
            logger.warning(f"Failed to load UI state cache: {e}")
            self._state = {}

    def _save_cache(self) -> None:
        """Save current state to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._state, f)
            logger.info("Saved UI state to cache")
        except Exception as e:
            logger.error(f"Failed to save UI state cache: {e}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get cached state for a key.

        Args:
            key: State key to retrieve
            default: Default value if key not found

        Returns:
            Cached state value or default
        """
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """
        Set state for a key and save to cache.

        Args:
            key: State key to set
            value: Value to cache
        """
        self._state[key] = value
        self._save_cache()

    def clear_state(self, key: Optional[str] = None) -> None:
        """
        Clear state for a key or all state.

        Args:
            key: Key to clear, or None to clear all
        """
        if key:
            self._state.pop(key, None)
        else:
            self._state.clear()
        self._save_cache()

    @lru_cache(maxsize=100)
    def get_cached_value(self, key: str, default: Any = None) -> Any:
        """
        Get a cached value with LRU caching.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        return self.get_state(key, default)

    def clear_lru_cache(self) -> None:
        """Clear the LRU cache."""
        self.get_cached_value.cache_clear()
