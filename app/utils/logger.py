"""
Logging configuration for TubeGrab.
Provides rotating file handler and console handler.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


_initialized = False
_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOG_FILE = _LOG_DIR / "tubegrab.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _initialize() -> None:
    """Set up root logger handlers once."""
    global _initialized
    if _initialized:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("tubegrab")
    root_logger.setLevel(logging.DEBUG)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger namespaced under 'tubegrab'.

    Args:
        name: Module or component name (e.g. 'ui.main_window').

    Returns:
        A configured Logger instance.
    """
    _initialize()
    full_name = f"tubegrab.{name}" if not name.startswith("tubegrab") else name
    return logging.getLogger(full_name)
