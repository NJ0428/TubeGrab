"""
UpdateWorker — background QThread for checking and optionally updating yt-dlp.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.core.updater import UpdateResult, check_latest_version, get_ytdlp_version, update_ytdlp
from app.utils.logger import get_logger

logger = get_logger("workers.update_worker")


class UpdateWorker(QThread):
    """Background thread that checks the yt-dlp version and optionally updates it.

    Signals:
        version_checked(current_version, latest_version): emitted after checking PyPI.
        update_finished(result): emits an UpdateResult as an object signal.
        error(message): emitted on unexpected failure.
    """

    version_checked = Signal(str, str)
    update_finished = Signal(object)
    error = Signal(str)

    def __init__(self, auto_update: bool = False, parent: object = None) -> None:
        super().__init__(parent)
        self._auto_update = auto_update

    def run(self) -> None:
        """Thread entry point: check version, optionally update, emit results."""
        try:
            current = get_ytdlp_version()
            latest = check_latest_version()

            self.version_checked.emit(current, latest)
            logger.debug(
                "Version check complete — current=%s latest=%s auto_update=%s",
                current,
                latest,
                self._auto_update,
            )

            if self._auto_update and latest and latest != current:
                result = update_ytdlp()
                self.update_finished.emit(result)
            else:
                # No-op result: just report current state
                if latest and latest != current:
                    msg = f"yt-dlp update available: {current} \u2192 {latest}"
                else:
                    msg = f"yt-dlp is up to date ({current})"
                result = UpdateResult(
                    success=True,
                    old_version=current,
                    new_version=current,
                    message=msg,
                    updated=False,
                )
                self.update_finished.emit(result)
        except Exception as exc:
            logger.error("UpdateWorker unexpected error: %s", exc)
            self.error.emit(str(exc))
