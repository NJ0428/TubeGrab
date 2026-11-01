"""
ClipboardBanner — dismissible notification banner for clipboard URL detection.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class ClipboardBanner(QFrame):
    """A compact dismissible banner shown when a YouTube URL is detected in the clipboard.

    Signals:
        use_requested(str): Emitted with the URL when the user clicks "Use This URL".
        dismissed():        Emitted when the user clicks the dismiss button.
    """

    use_requested: Signal = Signal(str)
    dismissed: Signal = Signal()

    def __init__(self, url: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._url: str = url
        self.setObjectName("clipboardBanner")
        self.setFixedHeight(52)
        self._build_ui()
        if url:
            self._url_label.setText(self._truncate(url))

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # Clipboard icon
        icon_lbl = QLabel("\U0001f4cb")  # 📋
        icon_lbl.setFixedWidth(20)
        layout.addWidget(icon_lbl)

        # Descriptive label
        desc_lbl = QLabel("YouTube URL detected in clipboard:")
        desc_lbl.setObjectName("infoMeta")
        layout.addWidget(desc_lbl)

        # URL label (truncated, bold, accent colour via QSS objectName)
        self._url_label = QLabel("")
        self._url_label.setObjectName("clipboardUrl")
        layout.addWidget(self._url_label, stretch=1)

        # "Use This URL" button
        self._use_btn = QPushButton("Use This URL")
        self._use_btn.setObjectName("fetchButton")
        self._use_btn.setFixedHeight(32)
        self._use_btn.clicked.connect(self._on_use_clicked)
        layout.addWidget(self._use_btn)

        # Dismiss button
        self._dismiss_btn = QPushButton("\u2715")  # ✕
        self._dismiss_btn.setObjectName("iconButton")
        self._dismiss_btn.setFixedSize(32, 32)
        self._dismiss_btn.setToolTip("Dismiss")
        self._dismiss_btn.clicked.connect(self._on_dismiss_clicked)
        layout.addWidget(self._dismiss_btn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_url(self, url: str) -> None:
        """Update the displayed URL and stored value, then show the banner."""
        self._url = url
        self._url_label.setText(self._truncate(url))
        self.setVisible(True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate(url: str, max_len: int = 60) -> str:
        """Return *url* truncated to *max_len* characters with an ellipsis."""
        if len(url) <= max_len:
            return url
        return url[:max_len - 1] + "\u2026"  # …

    def _on_use_clicked(self) -> None:
        self.use_requested.emit(self._url)

    def _on_dismiss_clicked(self) -> None:
        self.dismissed.emit()
        self.hide()
