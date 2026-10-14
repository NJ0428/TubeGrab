"""
Input validation helpers for TubeGrab.
"""

from __future__ import annotations

import re

_YOUTUBE_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/watch\?.*v=[\w-]+|youtu\.be/[\w-]+)"
)

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def is_valid_youtube_url(url: str) -> bool:
    """Return True if *url* matches a YouTube watch or short-link pattern."""
    return bool(_YOUTUBE_PATTERN.search(url.strip()))


def sanitize_filename(name: str) -> str:
    """Remove illegal filename characters and truncate to 200 characters."""
    sanitized = _ILLEGAL_CHARS.sub("", name).strip()
    return sanitized[:200]
