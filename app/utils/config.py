"""
Application configuration manager for TubeGrab.
Persists settings to ~/.tubegrab/config.json.
"""

import json
import os
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

logger = get_logger("utils.config")

_CONFIG_DIR = Path.home() / ".tubegrab"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS: dict[str, Any] = {
    "download_path": str(Path.home() / "Downloads"),
    "default_resolution": "best",
    "default_format": "mp4",
    "max_concurrent_downloads": 3,
    "theme": "dark",
    "notify_on_complete": True,
}


class Config:
    """
    JSON-backed configuration store.

    Usage::

        cfg = Config()
        cfg.load()
        cfg.set("theme", "light")
        cfg.save()
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = dict(_DEFAULTS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load config from disk, falling back to defaults for missing keys."""
        try:
            if _CONFIG_FILE.exists():
                with _CONFIG_FILE.open("r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                # Merge stored values on top of defaults so new keys always exist
                for key, default_value in _DEFAULTS.items():
                    self._data[key] = stored.get(key, default_value)
                logger.debug("Config loaded from %s", _CONFIG_FILE)
            else:
                logger.debug("No config file found; using defaults")
                self._data = dict(_DEFAULTS)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load config (%s); using defaults", exc)
            self._data = dict(_DEFAULTS)

    def save(self) -> None:
        """Persist current config to disk."""
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with _CONFIG_FILE.open("w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            logger.debug("Config saved to %s", _CONFIG_FILE)
        except OSError as exc:
            logger.error("Failed to save config: %s", exc)

    def get(self, key: str) -> Any:
        """
        Return the value for *key*.

        Falls back to the default if the key is not found.

        Args:
            key: Configuration key name.

        Returns:
            The stored or default value, or ``None`` if unknown.
        """
        return self._data.get(key, _DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        """
        Set *key* to *value* in memory (call :meth:`save` to persist).

        Args:
            key:   Configuration key name.
            value: New value to store.
        """
        self._data[key] = value
        logger.debug("Config key '%s' set to %r", key, value)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def all(self) -> dict[str, Any]:
        """Return a shallow copy of the entire configuration dict."""
        return dict(self._data)

    def reset_to_defaults(self) -> None:
        """Restore all settings to their factory defaults."""
        self._data = dict(_DEFAULTS)
        logger.info("Config reset to defaults")
