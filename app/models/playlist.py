"""
PlaylistEntry and PlaylistInfo dataclasses for TubeGrab playlist support.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlaylistEntry:
    """Represents a single video entry within a playlist."""

    index: int          # 1-based position in playlist
    url: str
    title: str
    duration: int       # seconds, 0 if unknown
    thumbnail_url: str

    @property
    def duration_str(self) -> str:
        """Return duration as 'H:MM:SS' when >= 1 hour, else 'MM:SS'."""
        total = max(0, int(self.duration))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


@dataclass
class PlaylistInfo:
    """Holds metadata for a YouTube playlist and all its entries."""

    url: str
    title: str
    channel: str
    entries: list[PlaylistEntry] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.entries)
