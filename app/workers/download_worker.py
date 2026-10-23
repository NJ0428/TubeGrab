"""
DownloadWorker — QThread worker that drives a single DownloadTask.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.core.downloader import Downloader
from app.models.download_task import DownloadTask
from app.utils.logger import get_logger

logger = get_logger("workers.download_worker")


class DownloadWorker(QThread):
    """Executes a DownloadTask in a background thread.

    Signals:
        progress_updated: (task_id, progress_pct, speed, eta,
                           downloaded_bytes, total_bytes)
        finished:         (task_id) — download completed successfully.
        error:            (task_id, error_message) — download failed or was cancelled.
    """

    progress_updated: Signal = Signal(str, float, str, str, int, int)
    finished: Signal = Signal(str, str)
    error: Signal = Signal(str, str)

    def __init__(
        self,
        task: DownloadTask,
        ffmpeg_path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task = task
        self._ffmpeg_path = ffmpeg_path
        self._cancelled: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Request cancellation of the running download."""
        logger.info("Cancel requested for task: %s", self._task.task_id)
        self._cancelled = True

    # ------------------------------------------------------------------
    # Thread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Thread entry point — perform download and emit result signals."""
        task_id = self._task.task_id
        logger.debug("DownloadWorker started — task_id=%s", task_id)

        downloader = Downloader(ffmpeg_path=self._ffmpeg_path)

        def _progress_hook(d: dict) -> None:
            """Convert yt-dlp progress dict into a progress_updated signal."""
            if d.get("status") != "downloading":
                return

            downloaded_bytes: int = int(d.get("downloaded_bytes") or 0)
            total_bytes: int = int(
                d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            )
            speed: str = d.get("_speed_str") or ""
            eta: str = d.get("_eta_str") or ""

            if total_bytes > 0:
                progress_pct = (downloaded_bytes / total_bytes) * 100.0
            else:
                progress_pct = 0.0

            self.progress_updated.emit(
                task_id,
                progress_pct,
                speed,
                eta,
                downloaded_bytes,
                total_bytes,
            )

        cancel_check = lambda: self._cancelled  # noqa: E731

        try:
            _filepath = downloader.download(
                task=self._task,
                progress_callback=_progress_hook,
                cancel_check=cancel_check,
            )
            logger.info("DownloadWorker finished — task_id=%s path=%s", task_id, _filepath)
            self.finished.emit(task_id, _filepath or "")
        except Exception as exc:
            msg = str(exc)
            if "Cancelled" in msg:
                logger.info("Download cancelled — task_id=%s", task_id)
                self.error.emit(task_id, "Cancelled")
            else:
                logger.error(
                    "DownloadWorker error — task_id=%s error=%s", task_id, msg
                )
                self.error.emit(task_id, msg)
