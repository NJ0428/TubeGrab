"""
PlaylistWorker — QThread worker that fetches playlist metadata in the background.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.core.playlist import PlaylistFetcher
from app.models.playlist import PlaylistInfo
from app.utils.logger import get_logger

logger = get_logger("workers.playlist_worker")


class PlaylistWorker(QThread):
    """Runs PlaylistFetcher.fetch() in a background thread.

    Signals:
        finished: Emitted with the populated PlaylistInfo on success.
        error:    Emitted with an error message string on failure.
        progress: Emitted with (current, total) as each entry is processed.
    """

    finished: Signal = Signal(object)  # PlaylistInfo dataclass
    error: Signal = Signal(str)
    progress: Signal = Signal(int, int)  # (current, total)

    def __init__(self, url: str, parent=None) -> None:
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        """Thread entry point — fetch playlist metadata and emit the appropriate signal."""
        logger.debug("PlaylistWorker started for: %s", self._url)
        fetcher = PlaylistFetcher()

        def _progress_callback(current: int, total: int) -> None:
            self.progress.emit(current, total)

        try:
            playlist_info = fetcher.fetch(self._url, progress_callback=_progress_callback)
            logger.debug("PlaylistWorker finished for: %s", self._url)
            self.finished.emit(playlist_info)
        except ValueError as exc:
            logger.warning("PlaylistWorker error: %s", exc)
            self.error.emit(str(exc))
        except Exception as exc:
            logger.error("PlaylistWorker unexpected error: %s", exc)
            self.error.emit(f"Unexpected error: {exc}")
