"""
AboutDialog — displays application information.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class AboutDialog(QDialog):
    """Minimal about dialog displaying TubeGrab application information."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About TubeGrab")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # App name
        name_lbl = QLabel("TubeGrab")
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(22)
        name_lbl.setFont(name_font)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_lbl)

        # Version
        version_lbl = QLabel("Version 1.0.0")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setObjectName("infoMeta")
        layout.addWidget(version_lbl)

        layout.addSpacing(6)

        # Description
        desc_lbl = QLabel("A fast, modern YouTube downloader")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_lbl)

        layout.addSpacing(4)

        # Built with
        built_lbl = QLabel("Python \u00b7 PySide6 \u00b7 yt-dlp")
        built_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        built_lbl.setObjectName("infoMeta")
        layout.addWidget(built_lbl)

        layout.addSpacing(16)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        btn_row.addStretch(1)
        layout.addLayout(btn_row)
