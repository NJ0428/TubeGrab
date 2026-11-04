"""
HistoryDialog — full-featured download history browser for TubeGrab.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.history import HistoryManager
from app.models.history_entry import HistoryEntry
from app.utils.logger import get_logger

logger = get_logger("ui.dialogs.history_dialog")


class HistoryDialog(QDialog):
    """
    Modal dialog that displays the download history with search, date filter,
    re-download, and remove capabilities.
    """

    # Emitted when the user requests a re-download:
    # (url, resolution, format, save_path)
    redownload_requested: Signal = Signal(str, str, str, str)

    def __init__(
        self,
        history_manager: HistoryManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._history_manager = history_manager
        self._current_entries: list[HistoryEntry] = []

        self.setWindowTitle("Download History")
        self.setMinimumSize(800, 540)
        self.resize(900, 600)

        self._build_ui()
        self._load_table(self._history_manager.entries)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # ── Toolbar row ────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("searchInput")
        self._search_input.setPlaceholderText("Search by title or URL\u2026")
        self._search_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        toolbar.addWidget(self._search_input)

        self._search_btn = QPushButton("Search")
        self._search_btn.setObjectName("iconButton")
        self._search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self._search_btn)

        date_lbl = QLabel("Date:")
        toolbar.addWidget(date_lbl)

        self._date_input = QLineEdit()
        self._date_input.setObjectName("dateInput")
        self._date_input.setPlaceholderText("YYYY-MM-DD")
        self._date_input.setFixedWidth(110)
        toolbar.addWidget(self._date_input)

        self._filter_btn = QPushButton("Filter")
        self._filter_btn.setObjectName("iconButton")
        self._filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self._filter_btn)

        self._clear_filter_btn = QPushButton("Clear Filter")
        self._clear_filter_btn.setObjectName("iconButton")
        self._clear_filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self._clear_filter_btn)

        root.addLayout(toolbar)

        # ── Table ───────────────────────────────────────────────────────
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["Title", "Channel", "Resolution", "Format", "Size", "Date", "Actions"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setShowGrid(False)
        self._table.verticalHeader().hide()

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(1, 120)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 80)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(3, 60)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 80)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, 130)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 140)

        root.addWidget(self._table, stretch=1)

        # ── Bottom row ─────────────────────────────────────────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._entry_count_lbl = QLabel("0 entries")
        self._entry_count_lbl.setObjectName("infoMeta")
        bottom.addWidget(self._entry_count_lbl)

        bottom.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._clear_all_btn = QPushButton("Clear All History")
        self._clear_all_btn.setObjectName("clearBtn")
        self._clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self._clear_all_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self._close_btn)

        root.addLayout(bottom)

        # ── Connect signals ────────────────────────────────────────────
        self._search_btn.clicked.connect(self._on_search)
        self._search_input.returnPressed.connect(self._on_search)
        self._filter_btn.clicked.connect(self._on_filter_date)
        self._date_input.returnPressed.connect(self._on_filter_date)
        self._clear_filter_btn.clicked.connect(self._on_clear_filter)
        self._clear_all_btn.clicked.connect(self._on_clear_all)
        self._close_btn.clicked.connect(self.accept)

    # ------------------------------------------------------------------
    # Table helpers
    # ------------------------------------------------------------------

    def _load_table(self, entries: list[HistoryEntry]) -> None:
        """Clear and repopulate the table with the given entries."""
        self._current_entries = list(entries)
        self._table.setRowCount(0)

        for row_idx, entry in enumerate(self._current_entries):
            self._table.insertRow(row_idx)

            title_item = QTableWidgetItem(entry.title)
            title_item.setToolTip(entry.url)
            self._table.setItem(row_idx, 0, title_item)

            self._table.setItem(row_idx, 1, QTableWidgetItem(entry.channel))
            self._table.setItem(row_idx, 2, QTableWidgetItem(entry.resolution))
            self._table.setItem(row_idx, 3, QTableWidgetItem(entry.format.upper()))
            self._table.setItem(row_idx, 4, QTableWidgetItem(entry.file_size_str))
            self._table.setItem(row_idx, 5, QTableWidgetItem(entry.completed_at_display))

            # Actions cell
            actions_widget = self._make_actions_widget(entry)
            self._table.setCellWidget(row_idx, 6, actions_widget)
            self._table.setRowHeight(row_idx, 38)

        count = len(self._current_entries)
        self._entry_count_lbl.setText(f"{count} {'entry' if count == 1 else 'entries'}")
        logger.debug("History table loaded — %d rows", count)

    def _make_actions_widget(self, entry: HistoryEntry) -> QWidget:
        """Build and return the Actions cell widget for *entry*."""
        cell = QWidget()
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        redownload_btn = QPushButton("\u21ba Re-download")
        redownload_btn.setObjectName("iconButton")
        redownload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        redownload_btn.setFixedHeight(26)
        redownload_btn.clicked.connect(lambda checked=False, e=entry: self._on_redownload(e))
        layout.addWidget(redownload_btn)

        remove_btn = QPushButton("\u2715 Remove")
        remove_btn.setObjectName("clearBtn")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setFixedHeight(26)
        remove_btn.clicked.connect(lambda checked=False, tid=entry.task_id: self._on_remove(tid))
        layout.addWidget(remove_btn)

        return cell

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_search(self) -> None:
        """Filter the table by the current search query."""
        query = self._search_input.text().strip()
        results = self._history_manager.search(query)
        self._load_table(results)

    def _on_filter_date(self) -> None:
        """Filter the table by the current date string."""
        date_str = self._date_input.text().strip()
        results = self._history_manager.filter_by_date(date_str)
        self._load_table(results)

    def _on_clear_filter(self) -> None:
        """Clear all active filters and reload the full history."""
        self._search_input.clear()
        self._date_input.clear()
        self._load_table(self._history_manager.entries)

    def _on_redownload(self, entry: HistoryEntry) -> None:
        """Emit redownload_requested with this entry's details."""
        logger.info(
            "Re-download requested — url=%s resolution=%s format=%s path=%s",
            entry.url,
            entry.resolution,
            entry.format,
            entry.save_path,
        )
        self.redownload_requested.emit(
            entry.url,
            entry.resolution,
            entry.format,
            entry.save_path,
        )
        self.accept()

    def _on_remove(self, task_id: str) -> None:
        """Remove the entry identified by task_id and refresh the table."""
        self._history_manager.remove(task_id)
        # Re-apply any active search/date filter to stay consistent
        search_q = self._search_input.text().strip()
        date_q = self._date_input.text().strip()
        if search_q:
            self._load_table(self._history_manager.search(search_q))
        elif date_q:
            self._load_table(self._history_manager.filter_by_date(date_q))
        else:
            self._load_table(self._history_manager.entries)

    def _on_clear_all(self) -> None:
        """Ask for confirmation then clear the entire history."""
        reply = QMessageBox.question(
            self,
            "Clear All History",
            "Are you sure you want to delete all download history?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._history_manager.clear()
            self._load_table([])
            logger.info("All history cleared from dialog")
