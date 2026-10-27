"""
Input validation helpers for TubeGrab.
"""

from __future__ import annotations

import re

_YOUTUBE_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/watch\?.*v=[\w-]+|youtu\.be/[\w-]+)"
)

_PLAYLIST_PATTERN = re.compile(
    r"https?://(www\.)?(youtube\.com|youtu\.be)/.*[?&]list=((?!WL$|LL$)[\w-]+)"
)

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def is_valid_youtube_url(url: str) -> bool:
    """Return True if *url* matches a YouTube watch or short-link pattern."""
    return bool(_YOUTUBE_PATTERN.search(url.strip()))


def is_playlist_url(url: str) -> bool:
    """Return True if url is a YouTube playlist URL (contains list= parameter).

    Matches youtube.com/playlist?list=..., youtube.com/watch?...&list=...,
    youtu.be/...?list=... but excludes Watch Later (WL) and Liked Videos (LL).
    """
    return bool(_PLAYLIST_PATTERN.search(url.strip()))


def is_valid_url(url: str) -> bool:
    """Return True if url is a valid YouTube video OR playlist URL."""
    return is_valid_youtube_url(url) or is_playlist_url(url)


def sanitize_filename(name: str) -> str:
    """Remove illegal filename characters and truncate to 200 characters."""
    sanitized = _ILLEGAL_CHARS.sub("", name).strip()
    return sanitized[:200]
