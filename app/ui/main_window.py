"""
TubeGrab – Main Application Window
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.utils.config import Config
from app.utils.logger import get_logger

logger = get_logger("ui.main_window")

_STYLES_DIR = Path(__file__).resolve().parents[2] / "assets" / "styles"


class MainWindow(QMainWindow):
    """Primary application window for TubeGrab."""

    def __init__(self, config: Config | None = None) -> None:
        super().__init__()
        self._config = config or Config()
        self._config.load()
        self._current_theme: str = self._config.get("theme") or "dark"

        self._build_ui()
        self._connect_signals()
        logger.info("MainWindow initialised")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all widgets."""
        self.setWindowTitle("TubeGrab")
        self.setMinimumSize(900, 650)
        self.resize(1000, 720)

        # ── Central widget ──────────────────────────────────────────
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top bar ─────────────────────────────────────────────────
        root_layout.addWidget(self._build_top_bar())

        # ── Scrollable content area ─────────────────────────────────
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content_scroll.setObjectName("mainScrollArea")
        content_scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(14)

        # URL input section
        content_layout.addWidget(self._build_url_section())

        # Video info card (initially hidden)
        self._info_card = self._build_info_card()
        self._info_card.setVisible(False)
        content_layout.addWidget(self._info_card)

        # Download options
        content_layout.addWidget(self._build_download_options())

        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(sep)

        # Download list area
        content_layout.addWidget(self._build_download_list())

        # Push everything up
        content_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        content_scroll.setWidget(content_widget)
        root_layout.addWidget(content_scroll, stretch=1)

        # ── Status bar ──────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self._status_bar.setObjectName("statusBar")
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ── Top bar ────────────────────────────────────────────────────

    def _build_top_bar(self) -> QWidget:
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(56)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(10)

        # Logo / app title
        self._title_label = QLabel("TubeGrab")
        self._title_label.setObjectName("appTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        self._title_label.setFont(font)

        layout.addWidget(self._title_label)
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        # Theme toggle button
        self._theme_btn = QPushButton("☀ Light")
        self._theme_btn.setObjectName("iconButton")
        self._theme_btn.setToolTip("Toggle light / dark theme")
        self._theme_btn.setFixedHeight(32)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._theme_btn)

        # Settings button
        self._settings_btn = QPushButton("⚙ Settings")
        self._settings_btn.setObjectName("iconButton")
        self._settings_btn.setToolTip("Open settings")
        self._settings_btn.setFixedHeight(32)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._settings_btn)

        return top_bar

    # ── URL section ────────────────────────────────────────────────

    def _build_url_section(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        section_lbl = QLabel("VIDEO URL")
        section_lbl.setObjectName("sectionLabel")
        layout.addWidget(section_lbl)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._url_input = QLineEdit()
        self._url_input.setObjectName("urlInput")
        self._url_input.setPlaceholderText("Enter YouTube URL…")
        self._url_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        row.addWidget(self._url_input)

        self._paste_btn = QPushButton("Paste")
        self._paste_btn.setObjectName("iconButton")
        self._paste_btn.setToolTip("Paste URL from clipboard")
        self._paste_btn.setFixedWidth(60)
        self._paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self._paste_btn)

        self._fetch_btn = QPushButton("Fetch Info")
        self._fetch_btn.setObjectName("fetchButton")
        self._fetch_btn.setToolTip("Fetch video information")
        self._fetch_btn.setFixedWidth(100)
        self._fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self._fetch_btn)

        layout.addLayout(row)
        return card

    # ── Video info card ────────────────────────────────────────────

    def _build_info_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("infoCard")

        outer = QHBoxLayout(card)
        outer.setContentsMargins(12, 10, 12, 10)
        outer.setSpacing(14)

        # Thumbnail
        self._thumbnail_label = QLabel()
        self._thumbnail_label.setObjectName("thumbnailLabel")
        self._thumbnail_label.setFixedSize(160, 90)
        self._thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumbnail_label.setText("No Image")
        outer.addWidget(self._thumbnail_label)

        # Metadata
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(4)
        meta_layout.setContentsMargins(0, 0, 0, 0)

        self._info_title_lbl = QLabel("Video Title")
        self._info_title_lbl.setObjectName("infoTitle")
        self._info_title_lbl.setWordWrap(True)
        meta_layout.addWidget(self._info_title_lbl)

        self._info_channel_lbl = QLabel("Channel Name")
        self._info_channel_lbl.setObjectName("infoMeta")
        meta_layout.addWidget(self._info_channel_lbl)

        self._info_duration_lbl = QLabel("Duration: --:--")
        self._info_duration_lbl.setObjectName("infoMeta")
        meta_layout.addWidget(self._info_duration_lbl)

        meta_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        outer.addLayout(meta_layout, stretch=1)

        return card

    # ── Download options ───────────────────────────────────────────

    def _build_download_options(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        section_lbl = QLabel("DOWNLOAD OPTIONS")
        section_lbl.setObjectName("sectionLabel")
        layout.addWidget(section_lbl)

        # Row 1: resolution + format
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        res_lbl = QLabel("Resolution:")
        res_lbl.setFixedWidth(78)
        row1.addWidget(res_lbl)

        self._resolution_combo = QComboBox()
        self._resolution_combo.setObjectName("resolutionCombo")
        self._resolution_combo.addItems(
            ["Best", "2160p (4K)", "1440p (2K)", "1080p", "720p", "480p", "360p"]
        )
        self._resolution_combo.setFixedWidth(160)
        self._resolution_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self._resolution_combo)

        row1.addSpacerItem(
            QSpacerItem(20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        )

        fmt_lbl = QLabel("Format:")
        fmt_lbl.setFixedWidth(52)
        row1.addWidget(fmt_lbl)

        self._format_combo = QComboBox()
        self._format_combo.setObjectName("formatCombo")
        self._format_combo.addItems(["MP4", "WEBM", "MP3", "M4A"])
        self._format_combo.setFixedWidth(120)
        self._format_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self._format_combo)

        row1.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(row1)

        # Row 2: save path + browse
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        path_lbl = QLabel("Save to:")
        path_lbl.setFixedWidth(52)
        row2.addWidget(path_lbl)

        self._save_path_input = QLineEdit()
        self._save_path_input.setObjectName("savePathInput")
        self._save_path_input.setPlaceholderText("Select download folder…")
        default_path = self._config.get("download_path") or str(
            Path.home() / "Downloads"
        )
        self._save_path_input.setText(default_path)
        row2.addWidget(self._save_path_input)

        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setObjectName("iconButton")
        self._browse_btn.setToolTip("Choose download folder")
        self._browse_btn.setFixedWidth(80)
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self._browse_btn)

        layout.addLayout(row2)

        # Row 3: download button (centred)
        row3 = QHBoxLayout()
        row3.setSpacing(0)
        row3.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._download_btn = QPushButton("⬇  Download")
        self._download_btn.setObjectName("downloadButton")
        self._download_btn.setToolTip("Start downloading the video")
        self._download_btn.setFixedWidth(200)
        self._download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row3.addWidget(self._download_btn)

        row3.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        layout.addLayout(row3)

        return card

    # ── Download list ──────────────────────────────────────────────

    def _build_download_list(self) -> QWidget:
        container = QWidget()
        container.setObjectName("downloadListContainer")

        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(6)

        header_lbl = QLabel("DOWNLOADS")
        header_lbl.setObjectName("sectionLabel")
        outer_layout.addWidget(header_lbl)

        self._download_scroll = QScrollArea()
        self._download_scroll.setObjectName("downloadScroll")
        self._download_scroll.setWidgetResizable(True)
        self._download_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._download_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._download_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._download_scroll.setMinimumHeight(160)

        self._download_list_widget = QWidget()
        self._download_list_widget.setObjectName("downloadListWidget")
        self._download_list_layout = QVBoxLayout(self._download_list_widget)
        self._download_list_layout.setContentsMargins(0, 0, 0, 0)
        self._download_list_layout.setSpacing(4)
        self._download_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Placeholder when empty
        self._empty_lbl = QLabel("No downloads yet. Paste a URL above to get started.")
        self._empty_lbl.setObjectName("infoMeta")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._download_list_layout.addWidget(self._empty_lbl)

        self._download_scroll.setWidget(self._download_list_widget)
        outer_layout.addWidget(self._download_scroll)

        return container

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._paste_btn.clicked.connect(self._on_paste)
        self._fetch_btn.clicked.connect(self._on_fetch_info)
        self._browse_btn.clicked.connect(self._on_browse)
        self._download_btn.clicked.connect(self._on_download)
        self._theme_btn.clicked.connect(self._on_toggle_theme)
        self._settings_btn.clicked.connect(self._on_settings)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_paste(self) -> None:
        """Paste clipboard text into the URL input."""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self._url_input.setText(text)
            logger.debug("Pasted URL from clipboard: %s", text)
        else:
            self._status_bar.showMessage("Clipboard is empty.", 3000)

    def _on_fetch_info(self) -> None:
        """Placeholder: fetch video metadata."""
        url = self._url_input.text().strip()
        if not url:
            self._status_bar.showMessage("Please enter a URL first.", 3000)
            return
        logger.info("Fetch info requested for: %s", url)
        self._status_bar.showMessage(f"Fetching info for: {url}")
        # Show info card with placeholder data until worker is implemented
        self._info_title_lbl.setText("Fetching video information…")
        self._info_channel_lbl.setText("Channel: —")
        self._info_duration_lbl.setText("Duration: —")
        self._info_card.setVisible(True)

    def _on_browse(self) -> None:
        """Open folder browser and update save path."""
        current = self._save_path_input.text() or str(Path.home() / "Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._save_path_input.setText(folder)
            self._config.set("download_path", folder)
            self._config.save()
            logger.debug("Download path set to: %s", folder)

    def _on_download(self) -> None:
        """Placeholder: queue a download."""
        url = self._url_input.text().strip()
        if not url:
            self._status_bar.showMessage("Please enter a URL first.", 3000)
            return
        resolution = self._resolution_combo.currentText()
        fmt = self._format_combo.currentText()
        path = self._save_path_input.text().strip()
        logger.info(
            "Download requested — url=%s resolution=%s format=%s path=%s",
            url,
            resolution,
            fmt,
            path,
        )
        self._status_bar.showMessage(
            f"Queued: {url} [{resolution} / {fmt}]", 5000
        )
        # Remove "empty" placeholder and add a stub item
        self._empty_lbl.setVisible(False)
        self._add_download_item_stub(url, resolution, fmt)

    def _add_download_item_stub(self, url: str, resolution: str, fmt: str) -> None:
        """Add a placeholder download item to the list."""
        from PySide6.QtWidgets import QProgressBar

        item_frame = QFrame()
        item_frame.setObjectName("downloadItem")
        item_frame.setMinimumHeight(64)

        item_layout = QVBoxLayout(item_frame)
        item_layout.setContentsMargins(12, 8, 12, 8)
        item_layout.setSpacing(4)

        title_lbl = QLabel(url)
        title_lbl.setObjectName("infoTitle")
        title_lbl.setWordWrap(False)
        font = title_lbl.font()
        font.setPointSize(11)
        title_lbl.setFont(font)
        # Truncate long URLs for display
        if len(url) > 80:
            title_lbl.setText(url[:77] + "…")
        item_layout.addWidget(title_lbl)

        meta_lbl = QLabel(f"{resolution}  ·  {fmt}")
        meta_lbl.setObjectName("infoMeta")
        item_layout.addWidget(meta_lbl)

        progress = QProgressBar()
        progress.setValue(0)
        progress.setFormat("Queued")
        item_layout.addWidget(progress)

        self._download_list_layout.addWidget(item_frame)

    def _on_toggle_theme(self) -> None:
        """Switch between dark and light themes."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.load_theme(new_theme)
        logger.info("Theme toggled to: %s", new_theme)

    def _on_settings(self) -> None:
        """Placeholder: open settings dialog."""
        self._status_bar.showMessage("Settings – coming soon.", 3000)
        logger.debug("Settings button clicked")

    # ------------------------------------------------------------------
    # Theme management
    # ------------------------------------------------------------------

    def load_theme(self, theme: str) -> None:
        """
        Load and apply a QSS theme by name.

        Args:
            theme: ``"dark"`` or ``"light"``.
        """
        qss_path = _STYLES_DIR / f"{theme}.qss"
        if not qss_path.exists():
            logger.warning("Theme file not found: %s", qss_path)
            return

        try:
            qss = qss_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to read theme file %s: %s", qss_path, exc)
            return

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)

        self._current_theme = theme
        self._config.set("theme", theme)
        self._config.save()

        # Update toggle button label
        if theme == "dark":
            self._theme_btn.setText("☀ Light")
        else:
            self._theme_btn.setText("☾ Dark")

        logger.debug("Theme applied: %s", theme)
