"""
DownloadTask dataclass — represents a single download job.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.models.video import VideoInfo


@dataclass
class DownloadTask:
    video_info: VideoInfo
    resolution: str
    format: str
    save_path: str
    task_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "pending"
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error_message: str = ""
    output_file: str = ""
    subtitle_langs: list[str] = field(default_factory=list)  # e.g. ["ko", "en"]
    subtitle_format: str = ""                                  # "srt" or "vtt"
    subtitle_only: bool = False                                # download subtitle without video

    @property
    def total_bytes_str(self) -> str:
        """Return human-readable file size for total_bytes."""
        n = self.total_bytes
        if n <= 0:
            return "—"
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"
