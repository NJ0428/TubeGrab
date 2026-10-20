"""
DownloadItemWidget — card widget representing one download task.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from app.models.download_task import DownloadTask


class DownloadItemWidget(QFrame):
    cancel_requested = Signal(str)
    open_file_requested = Signal(str)
    retry_requested = Signal(str)

    def __init__(self, task: DownloadTask, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("downloadItem")
        self._task_id = task.task_id
        self._file_path = ""
        self._build_ui()
        self.update_task(task)

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(10)

        self._thumb_lbl = QLabel()
        self._thumb_lbl.setObjectName("thumbnailLabel")
        self._thumb_lbl.setFixedSize(80, 45)
        self._thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_lbl.setText("…")
        outer.addWidget(self._thumb_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(3)
        info_col.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = QLabel()
        self._title_lbl.setObjectName("infoTitle")
        self._title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        info_col.addWidget(self._title_lbl)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        info_col.addWidget(self._progress_bar)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self._speed_lbl = QLabel()
        self._speed_lbl.setObjectName("infoMeta")
        stats_row.addWidget(self._speed_lbl)

        self._eta_lbl = QLabel()
        self._eta_lbl.setObjectName("infoMeta")
        stats_row.addWidget(self._eta_lbl)

        self._size_lbl = QLabel()
        self._size_lbl.setObjectName("infoMeta")
        stats_row.addWidget(self._size_lbl)

        stats_row.addStretch(1)

        self._status_lbl = QLabel()
        self._status_lbl.setObjectName("infoMeta")
        stats_row.addWidget(self._status_lbl)

        info_col.addLayout(stats_row)
        outer.addLayout(info_col, stretch=1)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_col.setContentsMargins(0, 0, 0, 0)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setObjectName("iconButton")
        self._cancel_btn.setFixedWidth(64)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self._task_id))
        btn_col.addWidget(self._cancel_btn)

        self._open_btn = QPushButton("Open File")
        self._open_btn.setObjectName("iconButton")
        self._open_btn.setFixedWidth(64)
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(lambda: self.open_file_requested.emit(self._file_path))
        self._open_btn.setVisible(False)
        btn_col.addWidget(self._open_btn)

        self._retry_btn = QPushButton("Retry")
        self._retry_btn.setObjectName("iconButton")
        self._retry_btn.setFixedWidth(64)
        self._retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._retry_btn.clicked.connect(lambda: self.retry_requested.emit(self._task_id))
        self._retry_btn.setVisible(False)
        btn_col.addWidget(self._retry_btn)

        btn_col.addStretch(1)
        outer.addLayout(btn_col)

    def update_task(self, task: DownloadTask) -> None:
        """Refresh all UI elements from the given task snapshot."""
        title = task.video_info.title
        fm = self._title_lbl.fontMetrics()
        elided = fm.elidedText(title, Qt.TextElideMode.ElideRight, self._title_lbl.width() or 400)
        self._title_lbl.setText(elided)

        self._progress_bar.setValue(int(task.progress))

        self._speed_lbl.setText(task.speed or "")
        self._eta_lbl.setText(f"ETA: {task.eta}" if task.eta else "")

        if task.downloaded_bytes > 0:
            self._size_lbl.setText(f"{_fmt_bytes(task.downloaded_bytes)} / {task.total_bytes_str}")
        else:
            self._size_lbl.setText("")

        self._status_lbl.setText(task.status.capitalize())

        is_active = task.status in ("pending", "downloading")
        is_done = task.status == "completed"
        is_failed = task.status == "failed"

        self._cancel_btn.setVisible(is_active)
        self._open_btn.setVisible(is_done)
        self._retry_btn.setVisible(is_failed)

        if is_done:
            self._file_path = task.output_file or os.path.join(task.save_path, task.video_info.title)

        if task.error_message and is_failed:
            self._status_lbl.setToolTip(task.error_message)

        self._task_id = task.task_id

    def set_thumbnail(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            80, 45,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._thumb_lbl.setPixmap(scaled)


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
