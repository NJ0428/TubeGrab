"""
TubeGrab – Main Application Window (Phase 2)
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QFont
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

from app.models.download_task import DownloadTask
from app.models.video import VideoInfo
from app.ui.components.download_item import DownloadItemWidget
from app.ui.components.progress_card import ProgressCardWidget
from app.ui.components.url_input import UrlInputWidget
from app.ui.components.video_info import VideoInfoWidget
from app.ui.dialogs.settings_dialog import SettingsDialog
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
        self._video_info: VideoInfo | None = None
        self._download_items: dict[str, DownloadItemWidget] = {}

        self._build_ui()
        self._connect_signals()
        logger.info("MainWindow initialised")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.setWindowTitle("TubeGrab")
        self.setMinimumSize(900, 650)
        self.resize(1000, 720)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_top_bar())

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

        # URL input
        url_card = QFrame()
        url_card.setObjectName("card")
        url_card_layout = QVBoxLayout(url_card)
        url_card_layout.setContentsMargins(14, 12, 14, 12)
        url_card_layout.setSpacing(8)

        section_lbl = QLabel("VIDEO URL")
        section_lbl.setObjectName("sectionLabel")
        url_card_layout.addWidget(section_lbl)

        self._url_input = UrlInputWidget()
        url_card_layout.addWidget(self._url_input)
        content_layout.addWidget(url_card)

        # Video info
        info_card = QFrame()
        info_card.setObjectName("infoCard")
        info_card_layout = QVBoxLayout(info_card)
        info_card_layout.setContentsMargins(12, 10, 12, 10)
        info_card_layout.setSpacing(0)

        self._video_info_widget = VideoInfoWidget()
        info_card_layout.addWidget(self._video_info_widget)
        self._info_card = info_card
        self._info_card.setVisible(False)
        content_layout.addWidget(self._info_card)

        # Download options
        content_layout.addWidget(self._build_download_options())

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(sep)

        # Download list
        content_layout.addWidget(self._build_download_list())

        content_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        content_scroll.setWidget(content_widget)
        root_layout.addWidget(content_scroll, stretch=1)

        # Status bar with progress card
        self._status_bar = QStatusBar()
        self._status_bar.setObjectName("statusBar")
        self.setStatusBar(self._status_bar)

        self._progress_card = ProgressCardWidget()
        self._status_bar.addPermanentWidget(self._progress_card)
        self._status_bar.showMessage("Ready")

    def _build_top_bar(self) -> QWidget:
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(56)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 16, 0)
        layout.setSpacing(10)

        title_lbl = QLabel("TubeGrab")
        title_lbl.setObjectName("appTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title_lbl.setFont(font)
        layout.addWidget(title_lbl)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._theme_btn = QPushButton("☀ Light")
        self._theme_btn.setObjectName("iconButton")
        self._theme_btn.setToolTip("Toggle light / dark theme")
        self._theme_btn.setFixedHeight(32)
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._theme_btn)

        self._settings_btn = QPushButton("⚙ Settings")
        self._settings_btn.setObjectName("iconButton")
        self._settings_btn.setToolTip("Open settings")
        self._settings_btn.setFixedHeight(32)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._settings_btn)

        return top_bar

    def _build_download_options(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        section_lbl = QLabel("DOWNLOAD OPTIONS")
        section_lbl.setObjectName("sectionLabel")
        layout.addWidget(section_lbl)

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

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        path_lbl = QLabel("Save to:")
        path_lbl.setFixedWidth(52)
        row2.addWidget(path_lbl)

        self._save_path_input = QLineEdit()
        self._save_path_input.setObjectName("savePathInput")
        self._save_path_input.setPlaceholderText("Select download folder…")
        default_path = self._config.get("download_path") or str(Path.home() / "Downloads")
        self._save_path_input.setText(default_path)
        row2.addWidget(self._save_path_input)

        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setObjectName("iconButton")
        self._browse_btn.setToolTip("Choose download folder")
        self._browse_btn.setFixedWidth(80)
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self._browse_btn)

        layout.addLayout(row2)

        row3 = QHBoxLayout()
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
        self._download_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._download_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._download_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._download_scroll.setMinimumHeight(160)

        self._download_list_widget = QWidget()
        self._download_list_widget.setObjectName("downloadListWidget")
        self._download_list_layout = QVBoxLayout(self._download_list_widget)
        self._download_list_layout.setContentsMargins(0, 0, 0, 0)
        self._download_list_layout.setSpacing(4)
        self._download_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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
        self._url_input.fetch_requested.connect(self._on_fetch_requested)
        self._browse_btn.clicked.connect(self._on_browse)
        self._download_btn.clicked.connect(self._on_download_clicked)
        self._theme_btn.clicked.connect(self._on_toggle_theme)
        self._settings_btn.clicked.connect(self._on_settings)

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _on_fetch_requested(self, url: str) -> None:
        """Handle fetch_requested signal from UrlInputWidget."""
        logger.info("Fetch info requested for: %s", url)
        self._url_input.set_loading(True)
        self._status_bar.showMessage(f"Fetching info for: {url}")

        # Show info card with placeholder until real worker is implemented
        placeholder = VideoInfo(
            url=url,
            title="Fetching video information…",
            channel="—",
            duration=0,
            thumbnail_url="",
        )
        self._video_info = None
        self._video_info_widget.show_info(placeholder)
        self._info_card.setVisible(True)

        # Re-enable URL input after showing placeholder (real fetch would use worker)
        self._url_input.set_loading(False)
        self._status_bar.showMessage("Video info fetched (stub). Press Download to queue.", 4000)

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
            self._config.set("download_path", folder)
            self._config.save()
            logger.debug("Download path set to: %s", folder)

    def _on_download_clicked(self) -> None:
        """Queue a download when the Download button is pressed."""
        url = self._url_input.current_url()
        if not url:
            self._status_bar.showMessage("Please enter a URL first.", 3000)
            return

        video = self._video_info or VideoInfo(
            url=url,
            title=url,
            channel="Unknown",
            duration=0,
            thumbnail_url="",
        )

        resolution = self._resolution_combo.currentText()
        fmt = self._format_combo.currentText().lower()
        save_path = self._save_path_input.text().strip()

        task = DownloadTask(
            video_info=video,
            resolution=resolution,
            format=fmt,
            save_path=save_path,
            status="pending",
        )

        self.add_download_item(task)
        self._update_progress_card()

        logger.info(
            "Download queued — url=%s resolution=%s format=%s path=%s",
            url, resolution, fmt, save_path,
        )
        self._status_bar.showMessage(
            f"Queued: {video.title[:60]} [{resolution} / {fmt.upper()}]", 5000
        )

    def _on_toggle_theme(self) -> None:
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.load_theme(new_theme)
        logger.info("Theme toggled to: %s", new_theme)

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self._config, parent=self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.theme_changed.connect(self.load_theme)
        dialog.exec()

    def _on_settings_changed(self) -> None:
        default_path = self._config.get("download_path") or str(Path.home() / "Downloads")
        self._save_path_input.setText(default_path)
        logger.debug("Settings reloaded into main window")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def add_download_item(self, task: DownloadTask) -> None:
        """Insert a DownloadItemWidget for *task* into the list."""
        self._empty_lbl.setVisible(False)
        item = DownloadItemWidget(task)
        item.cancel_requested.connect(self._on_cancel_download)
        item.open_file_requested.connect(self._on_open_file)
        item.retry_requested.connect(self._on_retry_download)
        self._download_items[task.task_id] = item
        self._download_list_layout.addWidget(item)

    def _on_cancel_download(self, task_id: str) -> None:
        logger.info("Cancel requested for task: %s", task_id)
        self._status_bar.showMessage("Download cancelled.", 3000)

    def _on_open_file(self, file_path: str) -> None:
        import subprocess, sys
        logger.info("Open file requested: %s", file_path)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", file_path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", file_path])
            else:
                subprocess.Popen(["xdg-open", str(Path(file_path).parent)])
        except OSError as exc:
            logger.error("Failed to open file location: %s", exc)

    def _on_retry_download(self, task_id: str) -> None:
        logger.info("Retry requested for task: %s", task_id)
        self._status_bar.showMessage("Retry queued.", 3000)

    def _update_progress_card(self) -> None:
        total = len(self._download_items)
        active = sum(
            1 for w in self._download_items.values()
            if hasattr(w, "_task_id")
        )
        completed = 0
        self._progress_card.update_stats(total, active, completed)

    # ------------------------------------------------------------------
    # Theme management
    # ------------------------------------------------------------------

    def load_theme(self, theme: str) -> None:
        """Load and apply a QSS theme by name ('dark' or 'light')."""
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

        self._theme_btn.setText("☀ Light" if theme == "dark" else "☾ Dark")
        logger.debug("Theme applied: %s", theme)

    # ------------------------------------------------------------------
    # Window events
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        logger.info("TubeGrab shutting down")
        super().closeEvent(event)
