"""
FfmpegWarningDialog — shown when FFmpeg is not found on the system.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

_FFMPEG_DOWNLOAD_URL = "https://ffmpeg.org/download.html"


class FfmpegWarningDialog(QDialog):
    """Warning dialog displayed when FFmpeg is not found on the system."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FFmpeg Not Found")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        message_lbl = QLabel(
            "FFmpeg was not found on this system.\n\n"
            "Audio extraction (MP3/M4A) and some video merging features "
            "will not work.\n\n"
            "Please install FFmpeg and ensure it is in your PATH."
        )
        message_lbl.setWordWrap(True)
        layout.addWidget(message_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        download_btn = QPushButton("Download FFmpeg")
        download_btn.setObjectName("downloadButton")
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.clicked.connect(self._on_download_ffmpeg)
        btn_row.addWidget(download_btn)

        continue_btn = QPushButton("Continue Anyway")
        continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_btn.clicked.connect(self.accept)
        btn_row.addWidget(continue_btn)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_download_ffmpeg(self) -> None:
        """Open the FFmpeg download page in the default browser."""
        QDesktopServices.openUrl(QUrl(_FFMPEG_DOWNLOAD_URL))
