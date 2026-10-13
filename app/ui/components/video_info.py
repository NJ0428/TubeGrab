"""
VideoInfoWidget — displays fetched video metadata with async thumbnail loading.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.models.video import VideoInfo


class _ThumbnailLoader(QObject):
    """Worker: fetches thumbnail bytes in a background thread."""

    finished = Signal(bytes)
    failed = Signal()

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url

    def run(self) -> None:
        try:
            import httpx
            response = httpx.get(self._url, timeout=10, follow_redirects=True)
            response.raise_for_status()
            self.finished.emit(response.content)
        except Exception:
            self.failed.emit()


class VideoInfoWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._loader: _ThumbnailLoader | None = None
        self._build_ui()
        self.hide()

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)

        self._thumbnail_lbl = QLabel()
        self._thumbnail_lbl.setObjectName("thumbnailLabel")
        self._thumbnail_lbl.setFixedSize(160, 90)
        self._thumbnail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail_lbl.setText("…")
        outer.addWidget(self._thumbnail_lbl)

        meta = QVBoxLayout()
        meta.setSpacing(4)
        meta.setContentsMargins(0, 0, 0, 0)

        self._title_lbl = QLabel()
        self._title_lbl.setObjectName("infoTitle")
        self._title_lbl.setWordWrap(True)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self._title_lbl.setFont(title_font)
        meta.addWidget(self._title_lbl)

        self._channel_lbl = QLabel()
        self._channel_lbl.setObjectName("infoMeta")
        meta.addWidget(self._channel_lbl)

        self._duration_lbl = QLabel()
        self._duration_lbl.setObjectName("infoMeta")
        meta.addWidget(self._duration_lbl)

        meta.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        outer.addLayout(meta, stretch=1)

    def show_info(self, video_info: VideoInfo) -> None:
        """Populate labels and start async thumbnail download."""
        self._title_lbl.setText(video_info.title)
        self._channel_lbl.setText(f"Channel: {video_info.channel}")
        self._duration_lbl.setText(f"Duration: {video_info.duration_str}")
        self._thumbnail_lbl.setText("…")

        self.show()
        self._load_thumbnail(video_info.thumbnail_url)

    def clear(self) -> None:
        """Hide widget and reset all labels."""
        self._cancel_thumbnail_load()
        self._title_lbl.setText("")
        self._channel_lbl.setText("")
        self._duration_lbl.setText("")
        self._thumbnail_lbl.setText("")
        self.hide()

    def _load_thumbnail(self, url: str) -> None:
        if not url:
            return
        self._cancel_thumbnail_load()

        self._thread = QThread()
        self._loader = _ThumbnailLoader(url)
        self._loader.moveToThread(self._thread)

        self._thread.started.connect(self._loader.run)
        self._loader.finished.connect(self._on_thumbnail_loaded)
        self._loader.failed.connect(self._on_thumbnail_failed)
        self._loader.finished.connect(self._thread.quit)
        self._loader.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_thumbnail_loaded(self, data: bytes) -> None:
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            scaled = pixmap.scaled(
                160, 90,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._thumbnail_lbl.setPixmap(scaled)
        else:
            self._thumbnail_lbl.setText("No Image")

    def _on_thumbnail_failed(self) -> None:
        self._thumbnail_lbl.setText("No Image")

    def _cancel_thumbnail_load(self) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        self._thread = None
        self._loader = None
