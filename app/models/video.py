"""
VideoInfo dataclass — holds metadata fetched from yt-dlp.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class VideoInfo:
    url: str
    title: str
    channel: str
    duration: int
    thumbnail_url: str
    formats: list[dict] = field(default_factory=list)
    available_resolutions: list[str] = field(default_factory=list)
    available_subtitles: dict[str, str] = field(default_factory=dict)

    @property
    def duration_str(self) -> str:
        """Return duration as 'H:MM:SS' when >= 1 hour, else 'MM:SS'."""
        total = max(0, int(self.duration))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
