"""
DownloadManager — orchestrates a queue of DownloadTasks with concurrency limiting.

Lives in the main thread (QObject, not QThread).  Worker threads are created here
and their signals are forwarded to callers via the manager's own signals.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from app.models.download_task import DownloadTask
from app.utils.config import Config
from app.utils.logger import get_logger
from app.workers.download_worker import DownloadWorker

logger = get_logger("core.download_manager")

_DEFAULT_MAX_CONCURRENT: int = 3


class DownloadManager(QObject):
    """Manages a task queue and a pool of concurrent DownloadWorkers.

    Signals:
        task_queued(str):                          task_id added to the queue.
        task_started(str):                         task_id whose download began.
        task_progress(str, float, str, str, int, int):
            (task_id, pct, speed, eta, downloaded_bytes, total_bytes)
        task_finished(str):                        task_id that completed successfully.
        task_failed(str, str):                     (task_id, error_message).
        task_cancelled(str):                       task_id that was cancelled.
        queue_changed(int, int, int):              (total, active, pending) after any state change.
    """

    task_queued: Signal = Signal(str)
    task_started: Signal = Signal(str)
    task_progress: Signal = Signal(str, float, str, str, int, int)
    task_finished: Signal = Signal(str, str)
    task_failed: Signal = Signal(str, str)
    task_cancelled: Signal = Signal(str)
    queue_changed: Signal = Signal(int, int, int)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        config: Config,
        ffmpeg_path: str | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._config: Config = config
        self._ffmpeg_path: str | None = ffmpeg_path
        self._tasks: dict[str, DownloadTask] = {}
        self._workers: dict[str, DownloadWorker] = {}
        self._queue: list[str] = []

        logger.debug("DownloadManager initialised (max_concurrent=%d)", self.max_concurrent)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def max_concurrent(self) -> int:
        """Maximum number of simultaneous downloads (read from config)."""
        value = self._config.get("max_concurrent_downloads")
        try:
            return int(value) if value is not None else _DEFAULT_MAX_CONCURRENT
        except (TypeError, ValueError):
            return _DEFAULT_MAX_CONCURRENT

    @property
    def active_count(self) -> int:
        """Number of workers currently running."""
        return len(self._workers)

    @property
    def pending_count(self) -> int:
        """Number of tasks waiting in the queue."""
        return len(self._queue)

    @property
    def total_count(self) -> int:
        """Total number of tasks known to the manager."""
        return len(self._tasks)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_task(self, task: DownloadTask) -> None:
        """Register *task*, add it to the pending queue and attempt to start it.

        Args:
            task: A fully constructed :class:`~app.models.download_task.DownloadTask`.
        """
        task.status = "pending"
        self._tasks[task.task_id] = task
        self._queue.append(task.task_id)
        logger.info("Task queued — task_id=%s url=%s", task.task_id, task.video_info.url)
        self.task_queued.emit(task.task_id)
        self._try_start_next()

    def cancel_task(self, task_id: str) -> None:
        """Cancel an active or pending task identified by *task_id*.

        If the task is currently downloading the worker's ``cancel()`` method is
        called.  If the task is still in the pending queue it is removed
        immediately and its status updated.

        Args:
            task_id: The UUID string of the task to cancel.
        """
        if task_id in self._workers:
            logger.info("Cancelling active worker — task_id=%s", task_id)
            self._workers[task_id].cancel()
            # The worker will emit error("Cancelled") which triggers _on_worker_error.
        elif task_id in self._queue:
            self._queue.remove(task_id)
            task = self._tasks.get(task_id)
            if task is not None:
                task.status = "cancelled"
            logger.info("Removed pending task from queue — task_id=%s", task_id)
            self.task_cancelled.emit(task_id)
            self.queue_changed.emit(self.total_count, self.active_count, self.pending_count)
        else:
            logger.warning("cancel_task called for unknown task_id=%s", task_id)

    def retry_task(self, task_id: str) -> None:
        """Re-queue a previously failed or cancelled task.

        The task's fields are reset to their initial values before re-queuing.

        Args:
            task_id: The UUID string of the task to retry.
        """
        task = self._tasks.get(task_id)
        if task is None:
            logger.warning("retry_task called for unknown task_id=%s", task_id)
            return

        # Reset all mutable state
        task.status = "pending"
        task.progress = 0.0
        task.speed = ""
        task.eta = ""
        task.downloaded_bytes = 0
        task.error_message = ""

        self._queue.append(task_id)
        logger.info("Task re-queued for retry — task_id=%s", task_id)
        self.task_queued.emit(task_id)
        self._try_start_next()

    def get_task(self, task_id: str) -> DownloadTask | None:
        """Return the :class:`~app.models.download_task.DownloadTask` for *task_id*, or ``None``."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[DownloadTask]:
        """Return a snapshot list of all tasks in insertion order."""
        return list(self._tasks.values())

    def cancel_all(self) -> None:
        """Cancel every active worker and discard the pending queue."""
        logger.info(
            "cancel_all — stopping %d worker(s), clearing %d queued task(s)",
            self.active_count,
            self.pending_count,
        )

        # Cancel workers first (they will call _on_worker_error asynchronously)
        for worker in list(self._workers.values()):
            worker.cancel()

        # Clear and mark pending tasks as cancelled
        for task_id in list(self._queue):
            task = self._tasks.get(task_id)
            if task is not None:
                task.status = "cancelled"
            self.task_cancelled.emit(task_id)

        self._queue.clear()
        self.queue_changed.emit(self.total_count, self.active_count, self.pending_count)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_start_next(self) -> None:
        """Start as many queued tasks as the concurrency limit allows."""
        while self.active_count < self.max_concurrent and self._queue:
            task_id = self._queue.pop(0)
            task = self._tasks.get(task_id)
            if task is None:
                logger.warning("Task in queue but not in _tasks — task_id=%s", task_id)
                continue

            worker = DownloadWorker(task, ffmpeg_path=self._ffmpeg_path, parent=self)

            # Wire up worker signals to manager slots, passing task_id via lambdas
            worker.progress_updated.connect(
                lambda tid, pct, spd, eta, dl, tot,
                _tid=task_id: self._on_worker_progress(_tid, pct, spd, eta, dl, tot)
            )
            worker.finished.connect(
                lambda tid, fp, _tid=task_id: self._on_worker_finished(_tid, fp)
            )
            worker.error.connect(
                lambda tid, msg, _tid=task_id: self._on_worker_error(_tid, msg)
            )

            self._workers[task_id] = worker
            task.status = "downloading"
            worker.start()

            logger.info(
                "Worker started — task_id=%s active=%d pending=%d",
                task_id, self.active_count, self.pending_count,
            )
            self.task_started.emit(task_id)
            self.queue_changed.emit(self.total_count, self.active_count, self.pending_count)

    # ------------------------------------------------------------------
    # Worker signal handlers
    # ------------------------------------------------------------------

    def _on_worker_progress(
        self,
        task_id: str,
        pct: float,
        speed: str,
        eta: str,
        dl: int,
        total: int,
    ) -> None:
        """Forward progress data to the task object and emit task_progress."""
        task = self._tasks.get(task_id)
        if task is not None:
            task.progress = pct
            task.speed = speed
            task.eta = eta
            task.downloaded_bytes = dl
            task.total_bytes = total
        self.task_progress.emit(task_id, pct, speed, eta, dl, total)

    def _on_worker_finished(self, task_id: str, file_path: str) -> None:
        """Handle successful completion of a worker."""
        task = self._tasks.get(task_id)
        if task is not None:
            task.status = "completed"
            task.progress = 100.0
            task.output_file = file_path

        self._workers.pop(task_id, None)
        logger.info("Task completed — task_id=%s", task_id)
        self.task_finished.emit(task_id, file_path)
        self.queue_changed.emit(self.total_count, self.active_count, self.pending_count)
        self._try_start_next()

    def _on_worker_error(self, task_id: str, msg: str) -> None:
        """Handle a worker failure or cancellation."""
        task = self._tasks.get(task_id)
        if task is not None:
            task.error_message = msg
            if msg == "Cancelled":
                task.status = "cancelled"
            else:
                task.status = "failed"

        self._workers.pop(task_id, None)

        if msg == "Cancelled":
            logger.info("Task cancelled — task_id=%s", task_id)
            self.task_cancelled.emit(task_id)
        else:
            logger.error("Task failed — task_id=%s error=%s", task_id, msg)
            self.task_failed.emit(task_id, msg)

        self.queue_changed.emit(self.total_count, self.active_count, self.pending_count)
        self._try_start_next()
