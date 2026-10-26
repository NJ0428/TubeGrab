"""
PlaylistDialog — lets the user select individual videos from a playlist
and configure download options before queuing them.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
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
    QVBoxLayout,
    QWidget,
)

from app.models.playlist import PlaylistInfo
from app.utils.config import Config
from app.utils.logger import get_logger

logger = get_logger("ui.dialogs.playlist_dialog")


class PlaylistDialog(QDialog):
    """Dialog for selecting and downloading videos from a playlist."""

    # Emits: selected_urls, resolution, fmt, save_path
    download_requested = Signal(list, str, str, str)

    def __init__(
        self,
        playlist_info: PlaylistInfo,
        config: Config,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._playlist_info = playlist_info
        self._config = config

        self.setWindowTitle("Playlist Download")
        self.setMinimumSize(700, 500)
        self.resize(780, 560)

        self._build_ui()
        self._populate_table()
        self._on_selection_changed()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # Header
        root.addWidget(self._build_header())

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["", "#", "Title", "Duration"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(32)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 32)
        self._table.setColumnWidth(1, 40)
        self._table.setColumnWidth(3, 75)

        root.addWidget(self._table)

        # Toolbar row
        root.addLayout(self._build_toolbar_row())

        # Save path row
        root.addLayout(self._build_save_path_row())

        # Bottom buttons
        root.addLayout(self._build_button_row())

    def _build_header(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(2)

        title_lbl = QLabel(self._playlist_info.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_lbl.setFont(title_font)
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)

        channel_lbl = QLabel(self._playlist_info.channel)
        channel_lbl.setObjectName("infoMeta")
        meta_row.addWidget(channel_lbl)

        count_lbl = QLabel(f"{self._playlist_info.total_count} videos")
        count_lbl.setObjectName("infoMeta")
        meta_row.addWidget(count_lbl)

        meta_row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(meta_row)

        return container

    def _build_toolbar_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        select_all_btn = QPushButton("Select All")
        select_all_btn.setFixedWidth(90)
        select_all_btn.clicked.connect(self._on_select_all)
        row.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.setFixedWidth(90)
        deselect_all_btn.clicked.connect(self._on_deselect_all)
        row.addWidget(deselect_all_btn)

        self._selected_label = QLabel("0 selected")
        self._selected_label.setObjectName("infoMeta")
        row.addWidget(self._selected_label)

        row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        res_lbl = QLabel("Resolution:")
        row.addWidget(res_lbl)

        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(["Best", "1080p", "720p", "480p", "360p"])
        self._resolution_combo.setFixedWidth(110)
        row.addWidget(self._resolution_combo)

        fmt_lbl = QLabel("Format:")
        row.addWidget(fmt_lbl)

        self._format_combo = QComboBox()
        self._format_combo.addItems(["MP4", "WEBM", "MP3", "M4A"])
        self._format_combo.setFixedWidth(90)
        row.addWidget(self._format_combo)

        return row

    def _build_save_path_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        path_lbl = QLabel("Save to:")
        path_lbl.setFixedWidth(52)
        row.addWidget(path_lbl)

        default_path = self._config.get("download_path") or str(Path.home() / "Downloads")
        self._save_path_input = QLineEdit(default_path)
        self._save_path_input.setObjectName("savePathInput")
        self._save_path_input.setPlaceholderText("Select download folder…")
        row.addWidget(self._save_path_input)

        browse_btn = QPushButton("Browse…")
        browse_btn.setObjectName("iconButton")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._on_browse)
        row.addWidget(browse_btn)

        return row

    def _build_button_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(90)
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(cancel_btn)

        self._download_btn = QPushButton("Download Selected (0)")
        self._download_btn.setObjectName("downloadButton")
        self._download_btn.setFixedWidth(210)
        self._download_btn.setEnabled(False)
        self._download_btn.clicked.connect(self._on_download)
        row.addWidget(self._download_btn)

        return row

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        entries = self._playlist_info.entries
        self._table.setRowCount(len(entries))
        self._checkboxes: list[QCheckBox] = []

        for row_idx, entry in enumerate(entries):
            self._table.setRowHeight(row_idx, 32)

            # Checkbox column
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_selection_changed)
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_layout.setContentsMargins(4, 0, 4, 0)
            self._table.setCellWidget(row_idx, 0, cell_widget)
            self._checkboxes.append(checkbox)

            # Index column
            index_item = QTableWidgetItem(str(entry.index))
            index_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row_idx, 1, index_item)

            # Title column (truncate for display)
            title_text = entry.title if len(entry.title) <= 80 else entry.title[:77] + "…"
            title_item = QTableWidgetItem(title_text)
            title_item.setToolTip(entry.title)
            self._table.setItem(row_idx, 2, title_item)

            # Duration column
            dur_item = QTableWidgetItem(entry.duration_str)
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row_idx, 3, dur_item)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_select_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(True)
        self._on_selection_changed()

    def _on_deselect_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(False)
        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        count = sum(1 for cb in self._checkboxes if cb.isChecked())
        self._selected_label.setText(f"{count} selected")
        self._download_btn.setText(f"Download Selected ({count})")
        self._download_btn.setEnabled(count > 0)

    def _on_download(self) -> None:
        selected_urls = [
            self._playlist_info.entries[i].url
            for i, cb in enumerate(self._checkboxes)
            if cb.isChecked()
        ]
        if not selected_urls:
            return

        resolution = self._resolution_combo.currentText()
        fmt = self._format_combo.currentText()
        save_path = self._save_path_input.text().strip()

        logger.info(
            "Playlist download requested — %d videos, resolution=%s fmt=%s",
            len(selected_urls),
            resolution,
            fmt,
        )
        self.download_requested.emit(selected_urls, resolution, fmt, save_path)
        self.accept()

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
