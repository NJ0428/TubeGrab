"""
FFmpeg detection utilities for TubeGrab.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("core.ffmpeg")

# Common installation paths to probe in addition to PATH
_COMMON_LOCATIONS: list[str] = [
    "C:/ffmpeg/bin",
    "C:/ffmpeg",
    "C:/Program Files/ffmpeg/bin",
    "C:/Program Files (x86)/ffmpeg/bin",
    str(Path.home() / "ffmpeg" / "bin"),
    str(Path.home() / "ffmpeg"),
    "/usr/local/bin",
    "/usr/bin",
    "/opt/homebrew/bin",
    "/opt/local/bin",
]

_EXECUTABLE = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"


def find_ffmpeg() -> str | None:
    """Search PATH and common install locations for the ffmpeg executable.

    Returns:
        Absolute path string to the ffmpeg executable, or None if not found.
    """
    # 1. Check PATH first (handles the common case)
    found_in_path = shutil.which("ffmpeg")
    if found_in_path:
        logger.debug("ffmpeg found in PATH: %s", found_in_path)
        return found_in_path

    # 2. Probe common installation directories
    for directory in _COMMON_LOCATIONS:
        candidate = Path(directory) / _EXECUTABLE
        if candidate.is_file():
            path_str = str(candidate)
            logger.debug("ffmpeg found at: %s", path_str)
            return path_str

    logger.warning("ffmpeg not found on this system")
    return None


def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available on this system.

    Returns:
        True if ffmpeg can be located, False otherwise.
    """
    return find_ffmpeg() is not None


def get_ffmpeg_version() -> str:
    """Return the ffmpeg version string, or 'not found' if unavailable.

    Returns:
        A version string like '6.1' or 'not found'.
    """
    path = find_ffmpeg()
    if path is None:
        return "not found"

    try:
        result = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # First line is typically: "ffmpeg version 6.1 Copyright ..."
        first_line = result.stdout.splitlines()[0] if result.stdout else ""
        if first_line.startswith("ffmpeg version"):
            parts = first_line.split()
            if len(parts) >= 3:
                return parts[2]
        return first_line or "unknown"
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.error("Failed to query ffmpeg version: %s", exc)
        return "unknown"
