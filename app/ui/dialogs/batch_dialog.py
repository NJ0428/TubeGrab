"""
BatchDialog — lets the user paste multiple URLs at once and preview
which are valid before queuing them all in one shot.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from app.utils.config import Config
from app.utils.validators import is_playlist_url, is_valid_url


class BatchDialog(QDialog):
    """Dialog for pasting multiple YouTube URLs and queuing them at once."""

    # (valid_urls, resolution, fmt, save_path)
    batch_download_requested: Signal = Signal(list, str, str, str)

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config

        self.setWindowTitle("Batch URL Input")
        self.setMinimumSize(680, 520)

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(10)

        # Section title
        title_lbl = QLabel("BATCH URL INPUT")
        title_lbl.setObjectName("sectionLabel")
        root.addWidget(title_lbl)

        # Instructions
        info_lbl = QLabel(
            "Paste one URL per line. Invalid URLs will be automatically filtered out."
        )
        info_lbl.setObjectName("infoMeta")
        root.addWidget(info_lbl)

        # URL text area
        self._text_edit = QTextEdit()
        self._text_edit.setObjectName("batchUrlInput")
        self._text_edit.setPlaceholderText(
            "https://www.youtube.com/watch?v=...\n"
            "https://www.youtube.com/watch?v=...\n"
            "..."
        )
        self._text_edit.setAcceptRichText(False)
        self._text_edit.setMinimumHeight(160)
        root.addWidget(self._text_edit)

        # Analyze row
        analyze_row = QHBoxLayout()
        analyze_row.setSpacing(10)

        self._analyze_btn = QPushButton("Analyze URLs")
        self._analyze_btn.setObjectName("fetchButton")
        self._analyze_btn.setFixedWidth(120)
        self._analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        analyze_row.addWidget(self._analyze_btn)

        self._status_lbl = QLabel("")
        self._status_lbl.setObjectName("infoMeta")
        analyze_row.addWidget(self._status_lbl)

        analyze_row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        root.addLayout(analyze_row)

        # Preview table
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Status", "URL", "Type"])
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().hide()
        self._table.setShowGrid(False)
        self._table.setMinimumHeight(160)

        h_header = self._table.horizontalHeader()
        h_header.resizeSection(0, 40)
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.resizeSection(2, 80)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

        root.addWidget(self._table)

        # Download options row
        opts_row = QHBoxLayout()
        opts_row.setSpacing(10)

        res_lbl = QLabel("Resolution:")
        opts_row.addWidget(res_lbl)

        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(["Best", "1080p", "720p", "480p", "360p"])
        self._resolution_combo.setFixedWidth(140)
        self._resolution_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        opts_row.addWidget(self._resolution_combo)

        fmt_lbl = QLabel("Format:")
        opts_row.addWidget(fmt_lbl)

        self._format_combo = QComboBox()
        self._format_combo.addItems(["MP4", "WEBM", "MP3", "M4A"])
        self._format_combo.setFixedWidth(100)
        self._format_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        opts_row.addWidget(self._format_combo)

        opts_row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        root.addLayout(opts_row)

        # Save path row
        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        path_lbl = QLabel("Save to:")
        path_row.addWidget(path_lbl)

        self._save_path_input = QLineEdit()
        self._save_path_input.setObjectName("savePathInput")
        self._save_path_input.setPlaceholderText("Select download folder…")
        default_path = self._config.get("download_path") or str(
            Path.home() / "Downloads"
        )
        self._save_path_input.setText(default_path)
        path_row.addWidget(self._save_path_input)

        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setObjectName("iconButton")
        self._browse_btn.setToolTip("Choose download folder")
        self._browse_btn.setFixedWidth(80)
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        path_row.addWidget(self._browse_btn)
        root.addLayout(path_row)

        # Bottom button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._queue_lbl = QLabel("0 URLs will be queued")
        self._queue_lbl.setObjectName("infoMeta")
        btn_row.addWidget(self._queue_lbl)

        btn_row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._add_btn = QPushButton("Add to Queue (0)")
        self._add_btn.setObjectName("downloadButton")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setEnabled(False)
        btn_row.addWidget(self._add_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        root.addLayout(btn_row)

    def _connect_signals(self) -> None:
        self._analyze_btn.clicked.connect(self._on_analyze)
        self._browse_btn.clicked.connect(self._on_browse)
        self._add_btn.clicked.connect(self._on_add_to_queue)

        # Debounced auto-analyze on text change
        self._analyze_timer = QTimer(self)
        self._analyze_timer.setSingleShot(True)
        self._analyze_timer.setInterval(300)
        self._analyze_timer.timeout.connect(self._on_analyze)
        self._text_edit.textChanged.connect(lambda: self._analyze_timer.start())

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _parse_urls(
        self, text: str
    ) -> tuple[list[str], list[str], list[str]]:
        """Parse *text* into (valid_urls, invalid_urls, duplicate_urls).

        Splits on newlines, strips whitespace, skips blank lines.
        Deduplicates case-insensitively; first occurrence wins.
        """
        valid_urls: list[str] = []
        invalid_urls: list[str] = []
        duplicate_urls: list[str] = []
        seen: set[str] = set()

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            lower = stripped.lower()
            if lower in seen:
                duplicate_urls.append(stripped)
                continue
            seen.add(lower)

            if is_valid_url(stripped):
                valid_urls.append(stripped)
            else:
                invalid_urls.append(stripped)

        return valid_urls, invalid_urls, duplicate_urls

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_analyze(self) -> None:
        """Parse the current text and refresh the preview table."""
        text = self._text_edit.toPlainText()
        valid_urls, invalid_urls, duplicate_urls = self._parse_urls(text)

        # Rebuild table
        all_rows: list[tuple[str, str, str]] = []
        for url in valid_urls:
            url_type = "Playlist" if is_playlist_url(url) else "Video"
            all_rows.append(("valid", url, url_type))
        for url in invalid_urls:
            all_rows.append(("invalid", url, "—"))
        for url in duplicate_urls:
            all_rows.append(("duplicate", url, "—"))

        self._table.setRowCount(len(all_rows))
        for row_idx, (status, url, url_type) in enumerate(all_rows):
            if status == "valid":
                symbol = "✔"
                color = "#4caf50"
            elif status == "invalid":
                symbol = "✘"
                color = "#e94560"
            else:
                symbol = "⬛"
                color = "#a0a0b0"

            status_item = QTableWidgetItem(symbol)
            status_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            status_item.setForeground(
                __import__("PySide6.QtGui", fromlist=["QColor"]).QColor(color)
            )
            self._table.setItem(row_idx, 0, status_item)

            url_item = QTableWidgetItem(url)
            self._table.setItem(row_idx, 1, url_item)

            type_item = QTableWidgetItem(url_type)
            type_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row_idx, 2, type_item)

        # Update status label
        v = len(valid_urls)
        i = len(invalid_urls)
        d = len(duplicate_urls)
        parts: list[str] = []
        if v:
            parts.append(f"✔ {v} valid")
        if i:
            parts.append(f"✘ {i} invalid")
        if d:
            parts.append(f"⬛ {d} duplicate{'s' if d != 1 else ''}")
        self._status_lbl.setText("  ".join(parts) if parts else "")

        # Update queue label and button
        self._queue_lbl.setText(
            f"{v} URL{'s' if v != 1 else ''} will be queued"
        )
        self._add_btn.setText(f"Add to Queue ({v})")
        self._add_btn.setEnabled(v > 0)

    def _on_browse(self) -> None:
        current = self._save_path_input.text() or str(Path.home() / "Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._save_path_input.setText(folder)

    def _on_add_to_queue(self) -> None:
        text = self._text_edit.toPlainText()
        valid_urls, _, _ = self._parse_urls(text)
        if not valid_urls:
            return

        resolution = self._resolution_combo.currentText()
        fmt = self._format_combo.currentText()
        save_path = self._save_path_input.text().strip()

        self.batch_download_requested.emit(valid_urls, resolution, fmt, save_path)
        self.accept()
