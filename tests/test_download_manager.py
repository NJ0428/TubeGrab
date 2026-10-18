"""
Unit tests for app.core.download_manager.DownloadManager.

DownloadWorker is patched so no real threads or yt-dlp calls are made.
A QCoreApplication is created once for the test session because DownloadManager
is a QObject (signals require an event loop to exist).
"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch, call

# A QCoreApplication must exist before any QObject is instantiated.
from PySide6.QtCore import QCoreApplication

_app: QCoreApplication | None = None


def _ensure_app() -> None:
    global _app
    if QCoreApplication.instance() is None:
        _app = QCoreApplication(sys.argv)


_ensure_app()

from app.core.download_manager import DownloadManager  # noqa: E402  (after QApp)
from app.models.download_task import DownloadTask       # noqa: E402
from app.models.video import VideoInfo                  # noqa: E402
from app.utils.config import Config                     # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(max_concurrent: int = 3) -> Config:
    """Return a Config pre-loaded with the given max_concurrent_downloads."""
    cfg = Config()
    cfg.set("max_concurrent_downloads", max_concurrent)
    return cfg


def _make_video_info(url: str = "https://youtu.be/dQw4w9WgXcQ") -> VideoInfo:
    return VideoInfo(
        url=url,
        title="Test Video",
        channel="Test Channel",
        duration=180,
        thumbnail_url="",
    )


def _make_task(url: str = "https://youtu.be/dQw4w9WgXcQ") -> DownloadTask:
    return DownloadTask(
        video_info=_make_video_info(url),
        resolution="1080p",
        format="mp4",
        save_path="/tmp",
    )


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestDownloadManagerAddTask(unittest.TestCase):
    """test_add_task_queues_task — adding a task registers it correctly."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_add_task_queues_task(self, MockWorker: MagicMock) -> None:
        # Prevent the worker from actually starting
        mock_worker_instance = MagicMock()
        MockWorker.return_value = mock_worker_instance

        manager = DownloadManager(_make_config())
        task = _make_task()
        manager.add_task(task)

        self.assertIn(task.task_id, manager._tasks)
        # Worker should have been started (concurrency limit not yet hit)
        mock_worker_instance.start.assert_called_once()
        # Queue should be empty — task was popped and started immediately
        self.assertEqual(manager.pending_count, 0)
        self.assertEqual(manager.total_count, 1)


class TestDownloadManagerConcurrency(unittest.TestCase):
    """test_max_concurrent_respected — only N workers start simultaneously."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_max_concurrent_respected(self, MockWorker: MagicMock) -> None:
        # Each call to MockWorker() returns a fresh MagicMock
        workers = [MagicMock() for _ in range(3)]
        MockWorker.side_effect = workers

        manager = DownloadManager(_make_config(max_concurrent=1))
        tasks = [_make_task(f"https://youtu.be/vid{i}") for i in range(3)]

        for t in tasks:
            manager.add_task(t)

        # Only 1 worker should have been started
        started = sum(1 for w in workers if w.start.called)
        self.assertEqual(started, 1)

        # Remaining 2 tasks should be in the pending queue
        self.assertEqual(manager.pending_count, 2)
        self.assertEqual(manager.active_count, 1)


class TestDownloadManagerCancelPending(unittest.TestCase):
    """test_cancel_pending_task — cancelling a queued (not yet started) task."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_cancel_pending_task(self, MockWorker: MagicMock) -> None:
        manager = DownloadManager(_make_config(max_concurrent=0))
        task = _make_task()
        manager.add_task(task)

        # Task must be in the queue (max_concurrent=0 means nothing starts)
        self.assertIn(task.task_id, manager._queue)

        # Track signal emissions
        cancelled_ids: list[str] = []
        manager.task_cancelled.connect(lambda tid: cancelled_ids.append(tid))

        manager.cancel_task(task.task_id)

        self.assertNotIn(task.task_id, manager._queue)
        self.assertEqual(task.status, "cancelled")
        self.assertIn(task.task_id, cancelled_ids)


class TestDownloadManagerCancelActive(unittest.TestCase):
    """test_cancel_active_task — cancelling a running worker."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_cancel_active_task(self, MockWorker: MagicMock) -> None:
        mock_worker = MagicMock()
        MockWorker.return_value = mock_worker

        manager = DownloadManager(_make_config(max_concurrent=1))
        task = _make_task()
        manager.add_task(task)

        # Worker should be running
        self.assertIn(task.task_id, manager._workers)

        manager.cancel_task(task.task_id)

        mock_worker.cancel.assert_called_once()


class TestDownloadManagerRetry(unittest.TestCase):
    """test_retry_failed_task — re-queuing a failed task resets its state."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_retry_failed_task(self, MockWorker: MagicMock) -> None:
        mock_worker = MagicMock()
        MockWorker.return_value = mock_worker

        manager = DownloadManager(_make_config(max_concurrent=0))
        task = _make_task()
        manager.add_task(task)

        # Manually mark task as failed (simulating a previous failure)
        task.status = "failed"
        task.error_message = "Network error"
        task.progress = 45.0
        # Remove from queue to simulate it was popped but never ran
        if task.task_id in manager._queue:
            manager._queue.remove(task.task_id)

        queued_ids: list[str] = []
        manager.task_queued.connect(lambda tid: queued_ids.append(tid))

        manager.retry_task(task.task_id)

        self.assertEqual(task.status, "pending")
        self.assertEqual(task.progress, 0.0)
        self.assertEqual(task.error_message, "")
        # The task_queued signal should have fired
        self.assertIn(task.task_id, queued_ids)


class TestDownloadManagerQueueChangedSignal(unittest.TestCase):
    """test_queue_changed_emitted — queue_changed fires after add_task."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_queue_changed_emitted(self, MockWorker: MagicMock) -> None:
        mock_worker = MagicMock()
        MockWorker.return_value = mock_worker

        manager = DownloadManager(_make_config(max_concurrent=1))

        change_events: list[tuple[int, int, int]] = []
        manager.queue_changed.connect(
            lambda total, active, pending: change_events.append((total, active, pending))
        )

        task = _make_task()
        manager.add_task(task)

        # queue_changed should have been emitted at least once (when worker starts)
        self.assertTrue(len(change_events) > 0)
        # Most recent event: 1 total, 1 active, 0 pending
        last = change_events[-1]
        self.assertEqual(last[0], 1)   # total
        self.assertEqual(last[1], 1)   # active
        self.assertEqual(last[2], 0)   # pending


class TestDownloadManagerWorkerFinished(unittest.TestCase):
    """Verify internal _on_worker_finished updates task state and starts next."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_on_worker_finished_updates_task(self, MockWorker: MagicMock) -> None:
        mock_worker = MagicMock()
        MockWorker.return_value = mock_worker

        manager = DownloadManager(_make_config(max_concurrent=1))
        task = _make_task()
        manager.add_task(task)

        finished_ids: list[str] = []
        manager.task_finished.connect(lambda tid: finished_ids.append(tid))

        # Simulate worker finishing
        manager._on_worker_finished(task.task_id)

        self.assertEqual(task.status, "completed")
        self.assertEqual(task.progress, 100.0)
        self.assertNotIn(task.task_id, manager._workers)
        self.assertIn(task.task_id, finished_ids)


class TestDownloadManagerWorkerError(unittest.TestCase):
    """Verify internal _on_worker_error handles cancellation vs failure correctly."""

    @patch("app.core.download_manager.DownloadWorker")
    def test_on_worker_error_cancelled(self, MockWorker: MagicMock) -> None:
        mock_worker = MagicMock()
        MockWorker.return_value = mock_worker

        manager = DownloadManager(_make_config(max_concurrent=1))
        task = _make_task()
        manager.add_task(task)

        cancelled_ids: list[str] = []
        failed_calls: list[tuple[str, str]] = []
        manager.task_cancelled.connect(lambda tid: cancelled_ids.append(tid))
        manager.task_failed.connect(lambda tid, msg: failed_calls.append((tid, msg)))

        manager._on_worker_error(task.task_id, "Cancelled")

        self.assertEqual(task.status, "cancelled")
        self.assertIn(task.task_id, cancelled_ids)
        self.assertEqual(len(failed_calls), 0)

    @patch("app.core.download_manager.DownloadWorker")
    def test_on_worker_error_failure(self, MockWorker: MagicMock) -> None:
        mock_worker = MagicMock()
        MockWorker.return_value = mock_worker

        manager = DownloadManager(_make_config(max_concurrent=1))
        task = _make_task()
        manager.add_task(task)

        failed_calls: list[tuple[str, str]] = []
        manager.task_failed.connect(lambda tid, msg: failed_calls.append((tid, msg)))

        manager._on_worker_error(task.task_id, "Connection timed out")

        self.assertEqual(task.status, "failed")
        self.assertEqual(task.error_message, "Connection timed out")
        self.assertTrue(any(t == task.task_id for t, _ in failed_calls))


if __name__ == "__main__":
    unittest.main()
