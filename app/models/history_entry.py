"""
HistoryEntry dataclass — represents a completed download stored in history.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class HistoryEntry:
    task_id: str
    url: str
    title: str
    channel: str
    resolution: str
    format: str          # "mp4", "mp3", etc.
    save_path: str       # directory
    output_file: str     # full path to the file
    file_size: int       # bytes, 0 if unknown
    completed_at: str    # ISO 8601 datetime string e.g. "2024-01-15T14:30:00"

    @property
    def file_size_str(self) -> str:
        """Human-readable file size."""
        n = self.file_size
        if n <= 0:
            return "—"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    @property
    def completed_at_display(self) -> str:
        """Format completed_at as 'YYYY-MM-DD HH:MM' for display."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(self.completed_at)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return self.completed_at

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        """Deserialize from a plain dict."""
        return cls(**{k: d[k] for k in d if k in cls.__dataclass_fields__})
