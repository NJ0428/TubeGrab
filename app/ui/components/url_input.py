"""
URL input widget with clipboard paste, validity indicator, and fetch trigger.
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.utils.validators import is_playlist_url, is_valid_url, is_valid_youtube_url


class UrlInputWidget(QWidget):
    fetch_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._url_edit = QLineEdit()
        self._url_edit.setObjectName("urlLineEdit")
        self._url_edit.setPlaceholderText("Enter YouTube URL…")
        self._url_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        input_row.addWidget(self._url_edit)

        self._paste_btn = QPushButton("Paste")
        self._paste_btn.setObjectName("pasteBtn")
        self._paste_btn.setToolTip("Paste URL from clipboard")
        self._paste_btn.setFixedWidth(64)
        self._paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        input_row.addWidget(self._paste_btn)

        self._fetch_btn = QPushButton("Fetch Info")
        self._fetch_btn.setObjectName("fetchBtn")
        self._fetch_btn.setToolTip("Fetch video information")
        self._fetch_btn.setFixedWidth(100)
        self._fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fetch_btn.setEnabled(False)
        input_row.addWidget(self._fetch_btn)

        root.addLayout(input_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        self._valid_indicator = QLabel("")
        self._valid_indicator.setObjectName("urlValidIndicator")
        status_row.addWidget(self._valid_indicator)

        status_row.addStretch(1)

        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("urlProgressBar")
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setVisible(False)
        status_row.addWidget(self._progress_bar)

        root.addLayout(status_row)

    def _connect_signals(self) -> None:
        self._url_edit.textChanged.connect(self._on_text_changed)
        self._paste_btn.clicked.connect(self._on_paste)
        self._fetch_btn.clicked.connect(self._on_fetch)

    def _on_text_changed(self, text: str) -> None:
        stripped = text.strip()
        valid_video = is_valid_youtube_url(stripped)
        playlist = is_playlist_url(stripped)
        valid = valid_video or playlist

        self._fetch_btn.setEnabled(valid)

        if stripped:
            if valid_video and not playlist:
                self._valid_indicator.setText("✔ Valid URL")
                self._valid_indicator.setObjectName("urlValidValid")
                self._valid_indicator.setStyleSheet("")
            elif playlist:
                self._valid_indicator.setText("↳ Playlist detected")
                self._valid_indicator.setObjectName("urlValidPlaylist")
                self._valid_indicator.setStyleSheet("")
            else:
                self._valid_indicator.setText("✘ Invalid URL")
                self._valid_indicator.setObjectName("urlValidInvalid")
                self._valid_indicator.setStyleSheet("")
        else:
            self._valid_indicator.setText("")
            self._valid_indicator.setObjectName("urlValidIndicator")
            self._valid_indicator.setStyleSheet("")

    def _on_paste(self) -> None:
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self._url_edit.setText(text)

    def _on_fetch(self) -> None:
        url = self._url_edit.text().strip()
        if url and is_valid_url(url):
            self.fetch_requested.emit(url)

    def set_loading(self, loading: bool) -> None:
        """Show/hide indeterminate progress bar and toggle controls."""
        self._progress_bar.setVisible(loading)
        self._url_edit.setEnabled(not loading)
        self._paste_btn.setEnabled(not loading)
        if loading:
            self._fetch_btn.setEnabled(False)
        else:
            self._on_text_changed(self._url_edit.text())

    def current_url(self) -> str:
        """Return the current URL text."""
        return self._url_edit.text().strip()
