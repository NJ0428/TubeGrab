"""
MetadataWorker — QThread worker that fetches video metadata in the background.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.core.metadata import MetadataFetcher
from app.models.video import VideoInfo
from app.utils.logger import get_logger

logger = get_logger("workers.metadata_worker")


class MetadataWorker(QThread):
    """Runs MetadataFetcher.fetch() in a background thread.

    Signals:
        finished: Emitted with the populated VideoInfo on success.
        error:    Emitted with an error message string on failure.
    """

    finished: Signal = Signal(VideoInfo)
    error: Signal = Signal(str)

    def __init__(self, url: str, parent=None) -> None:
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        """Thread entry point — fetch metadata and emit the appropriate signal."""
        logger.debug("MetadataWorker started for: %s", self._url)
        fetcher = MetadataFetcher()
        try:
            video_info = fetcher.fetch(self._url)
            logger.debug("MetadataWorker finished for: %s", self._url)
            self.finished.emit(video_info)
        except ValueError as exc:
            logger.warning("MetadataWorker error: %s", exc)
            self.error.emit(str(exc))
        except Exception as exc:
            logger.error("MetadataWorker unexpected error: %s", exc)
            self.error.emit(f"Unexpected error: {exc}")
