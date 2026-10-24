"""
TubeGrab – Main Application Window (Phase 4)
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
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

from app.core.download_manager import DownloadManager
from app.core.ffmpeg import find_ffmpeg
from app.models.download_task import DownloadTask
from app.models.playlist import PlaylistInfo
from app.models.video import VideoInfo
from app.ui.components.download_item import DownloadItemWidget
from app.ui.components.progress_card import ProgressCardWidget
from app.ui.components.url_input import UrlInputWidget
from app.ui.components.video_info import VideoInfoWidget
from app.ui.dialogs.about_dialog import AboutDialog
from app.ui.dialogs.ffmpeg_dialog import FfmpegWarningDialog
from app.ui.dialogs.playlist_dialog import PlaylistDialog
from app.ui.dialogs.settings_dialog import SettingsDialog
from app.utils.config import Config
from app.utils.logger import get_logger
from app.utils.validators import is_playlist_url
from app.workers.metadata_worker import MetadataWorker
from app.workers.playlist_worker import PlaylistWorker

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
        self._metadata_worker: MetadataWorker | None = None
        self._playlist_worker: PlaylistWorker | None = None

        # Detect ffmpeg once at startup
        self._ffmpeg_path: str | None = find_ffmpeg()

        # Centralised download manager (owns all workers)
        self._download_manager = DownloadManager(
            self._config,
            self._ffmpeg_path,
            parent=self,
        )

        self._build_ui()
        self._connect_signals()

        if self._ffmpeg_path:
            logger.info("ffmpeg detected at: %s", self._ffmpeg_path)
        else:
            logger.warning("ffmpeg not found — audio post-processing will be unavailable")

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

        if self._ffmpeg_path is None:
            self._status_bar.showMessage(
                "Warning: ffmpeg not found — audio extraction may fail.", 8000
            )
            QTimer.singleShot(500, self._show_ffmpeg_warning)
        else:
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

        self._about_btn = QPushButton("ℹ About")
        self._about_btn.setObjectName("iconButton")
        self._about_btn.setToolTip("About TubeGrab")
        self._about_btn.setFixedHeight(32)
        self._about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self._about_btn)

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

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        header_lbl = QLabel("DOWNLOADS")
        header_lbl.setObjectName("sectionLabel")
        header_row.addWidget(header_lbl)

        header_row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        self._clear_btn = QPushButton("Clear Completed")
        self._clear_btn.setObjectName("clearBtn")
        self._clear_btn.setToolTip("Remove completed, failed, and cancelled items")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setFixedHeight(26)
        self._clear_btn.clicked.connect(self._on_clear_completed)
        header_row.addWidget(self._clear_btn)

        outer_layout.addLayout(header_row)

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
        # URL / metadata
        self._url_input.fetch_requested.connect(self._on_fetch_requested)

        # Download options toolbar
        self._browse_btn.clicked.connect(self._on_browse)
        self._download_btn.clicked.connect(self._on_download_clicked)

        # App-level
        self._theme_btn.clicked.connect(self._on_toggle_theme)
        self._about_btn.clicked.connect(self._on_about)
        self._settings_btn.clicked.connect(self._on_settings)

        # DownloadManager signals
        self._download_manager.task_progress.connect(self._on_download_progress)
        self._download_manager.task_finished.connect(self._on_download_finished)
        self._download_manager.task_failed.connect(self._on_download_error_from_manager)
        self._download_manager.task_cancelled.connect(self._on_download_cancelled)
        self._download_manager.queue_changed.connect(self._on_queue_changed)

    # ------------------------------------------------------------------
    # Slot handlers — metadata
    # ------------------------------------------------------------------

    def _on_fetch_requested(self, url: str) -> None:
        """Handle fetch_requested signal from UrlInputWidget."""
        logger.info("Fetch info requested for: %s", url)
        if is_playlist_url(url):
            self._start_playlist_fetch(url)
        else:
            self._start_metadata_fetch(url)

    def _start_metadata_fetch(self, url: str) -> None:
        """Stop any old worker, create a new MetadataWorker and start it."""
        if self._metadata_worker is not None and self._metadata_worker.isRunning():
            self._metadata_worker.finished.disconnect()
            self._metadata_worker.error.disconnect()
            self._metadata_worker.quit()
            self._metadata_worker.wait(3000)
            self._metadata_worker = None

        self._url_input.set_loading(True)
        self._status_bar.showMessage(f"Fetching info for: {url} …")

        worker = MetadataWorker(url, parent=self)
        worker.finished.connect(self._on_metadata_finished)
        worker.error.connect(self._on_metadata_error)
        self._metadata_worker = worker
        worker.start()

    def _start_playlist_fetch(self, url: str) -> None:
        """Stop any old playlist worker, create a new PlaylistWorker and start it."""
        if self._playlist_worker is not None and self._playlist_worker.isRunning():
            self._playlist_worker.finished.disconnect()
            self._playlist_worker.error.disconnect()
            self._playlist_worker.progress.disconnect()
            self._playlist_worker.quit()
            self._playlist_worker.wait(3000)
            self._playlist_worker = None

        self._url_input.set_loading(True)
        self._status_bar.showMessage("Fetching playlist info…")

        worker = PlaylistWorker(url, parent=self)
        worker.finished.connect(self._on_playlist_finished)
        worker.error.connect(self._on_playlist_error)
        worker.progress.connect(self._on_playlist_progress)
        self._playlist_worker = worker
        worker.start()

    def _on_metadata_finished(self, video_info: VideoInfo) -> None:
        """Slot: metadata fetched successfully."""
        self._video_info = video_info
        self._video_info_widget.show_info(video_info)
        self._info_card.setVisible(True)
        self._url_input.set_loading(False)

        # Populate the resolution combo with whatever this video actually offers
        self._resolution_combo.clear()
        if video_info.available_resolutions:
            self._resolution_combo.addItems(video_info.available_resolutions)
        else:
            self._resolution_combo.addItems(
                ["Best", "1080p", "720p", "480p", "360p"]
            )

        self._status_bar.showMessage(
            f"Ready — {video_info.title[:70]}", 6000
        )
        logger.info("Metadata displayed for: %s", video_info.title)

    def _on_metadata_error(self, msg: str) -> None:
        """Slot: metadata fetch failed."""
        self._url_input.set_loading(False)
        self._status_bar.showMessage(f"Error: {msg}", 8000)
        logger.warning("Metadata fetch error: %s", msg)

    # ------------------------------------------------------------------
    # Slot handlers — playlist
    # ------------------------------------------------------------------

    def _on_playlist_progress(self, current: int, total: int) -> None:
        """Slot: update status bar while playlist entries are being fetched."""
        self._status_bar.showMessage(f"Fetching playlist: {current}/{total} videos…")

    def _on_playlist_finished(self, playlist_info: PlaylistInfo) -> None:
        """Slot: playlist metadata fetched successfully — open the selection dialog."""
        self._url_input.set_loading(False)
        logger.info(
            "Playlist fetched — title=%r entries=%d",
            playlist_info.title,
            playlist_info.total_count,
        )

        dialog = PlaylistDialog(playlist_info, self._config, parent=self)
        dialog.download_requested.connect(self._on_playlist_download_requested)
        dialog.exec()

    def _on_playlist_error(self, msg: str) -> None:
        """Slot: playlist fetch failed."""
        self._url_input.set_loading(False)
        self._status_bar.showMessage(f"Playlist error: {msg}", 8000)
        logger.warning("Playlist fetch error: %s", msg)

    def _on_playlist_download_requested(
        self,
        urls: list,
        resolution: str,
        fmt: str,
        save_path: str,
    ) -> None:
        """Slot: user confirmed playlist download — queue all selected videos."""
        fmt_lower = fmt.lower()
        for url in urls:
            vi = VideoInfo(
                url=url,
                title=url,
                channel="",
                duration=0,
                thumbnail_url="",
            )
            task = DownloadTask(
                video_info=vi,
                resolution=resolution,
                format=fmt_lower,
                save_path=save_path,
            )
            self._download_manager.add_task(task)
            self.add_download_item(task)

        self._status_bar.showMessage(f"Queued {len(urls)} videos for download")
        logger.info(
            "Queued %d playlist videos — resolution=%s format=%s path=%s",
            len(urls),
            resolution,
            fmt_lower,
            save_path,
        )

    # ------------------------------------------------------------------
    # Slot handlers — download
    # ------------------------------------------------------------------

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
        """Queue a download via DownloadManager when the Download button is pressed."""
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
        )

        # Hand ownership to the manager and add the UI item
        self._download_manager.add_task(task)
        self.add_download_item(task)

        logger.info(
            "Download queued — url=%s resolution=%s format=%s path=%s",
            url, resolution, fmt, save_path,
        )

    def _on_cancel_download(self, task_id: str) -> None:
        """Slot: user clicked Cancel on a DownloadItemWidget."""
        logger.info("Cancel requested via UI — task_id=%s", task_id)
        self._download_manager.cancel_task(task_id)
        self._status_bar.showMessage("Cancelling download…", 3000)

    def _on_retry_download(self, task_id: str) -> None:
        """Re-queue a failed/cancelled download through the manager."""
        task = self._download_manager.get_task(task_id)
        if task is None:
            logger.warning("Retry requested but task not found: %s", task_id)
            self._status_bar.showMessage("Could not retry: task not found.", 3000)
            return

        self._download_manager.retry_task(task_id)

        # Update the existing item widget with the reset task state
        item = self._download_items.get(task_id)
        if item is not None:
            item.update_task(task)

        self._status_bar.showMessage("Retrying download…", 3000)
        logger.info("Retry requested for task: %s", task_id)

    def _on_download_progress(
        self,
        task_id: str,
        pct: float,
        speed: str,
        eta: str,
        downloaded_bytes: int,
        total_bytes: int,
    ) -> None:
        """Slot: update UI for in-progress download."""
        task = self._download_manager.get_task(task_id)
        if task is None:
            return

        item = self._download_items.get(task_id)
        if item is not None:
            item.update_task(task)

    def _on_download_finished(self, task_id: str, file_path: str) -> None:
        """Slot: a download completed successfully."""
        task = self._download_manager.get_task(task_id)
        if task is not None:
            item = self._download_items.get(task_id)
            if item is not None:
                item.update_task(task)
            title = task.video_info.title[:60]
        else:
            title = task_id

        self._status_bar.showMessage(f"Download complete: {title}", 6000)
        logger.info("Download finished — task_id=%s file_path=%s", task_id, file_path)

    def _on_download_error_from_manager(self, task_id: str, msg: str) -> None:
        """Slot: a download failed (non-cancellation error)."""
        task = self._download_manager.get_task(task_id)
        if task is not None:
            item = self._download_items.get(task_id)
            if item is not None:
                item.update_task(task)

        self._status_bar.showMessage(f"Download failed: {msg}", 8000)
        logger.error("Download failed — task_id=%s error=%s", task_id, msg)

    def _on_download_cancelled(self, task_id: str) -> None:
        """Slot: a download was cancelled."""
        task = self._download_manager.get_task(task_id)
        if task is not None:
            item = self._download_items.get(task_id)
            if item is not None:
                item.update_task(task)

        self._status_bar.showMessage("Download cancelled.", 4000)
        logger.info("Download cancelled — task_id=%s", task_id)

    def _on_queue_changed(self, total: int, active: int, pending: int) -> None:
        """Slot: update the progress card and status bar whenever queue state changes."""
        completed = total - active - pending
        # Clamp to avoid negative values if counts are momentarily inconsistent
        completed = max(0, completed)
        self._progress_card.update_stats(total, active, completed)

        if active > 0:
            self._status_bar.showMessage(
                f"Downloading {active} file(s) — {pending} queued", 0
            )

    def _on_open_file(self, file_path: str) -> None:
        import subprocess
        import sys
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

    def _on_about(self) -> None:
        """Open the About dialog."""
        dialog = AboutDialog(parent=self)
        dialog.exec()

    def _show_ffmpeg_warning(self) -> None:
        """Show the FFmpeg warning dialog (called via QTimer after main window appears)."""
        dialog = FfmpegWarningDialog(parent=self)
        dialog.exec()

    def _on_clear_completed(self) -> None:
        """Remove all completed, failed, and cancelled download items from the UI."""
        done_statuses = {"completed", "failed", "cancelled"}
        to_remove = [
            task_id
            for task_id, item in self._download_items.items()
            if self._download_manager.get_task(task_id) is not None
            and self._download_manager.get_task(task_id).status in done_statuses
        ]

        for task_id in to_remove:
            item = self._download_items.pop(task_id, None)
            if item is not None:
                self._download_list_layout.removeWidget(item)
                item.setParent(None)
                item.deleteLater()

        if not self._download_items:
            self._empty_lbl.setVisible(True)

        logger.debug("Cleared %d completed/failed/cancelled items", len(to_remove))

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

    def _update_progress_card(self) -> None:
        """Delegate to queue_changed counts sourced from the manager."""
        total = self._download_manager.total_count
        active = self._download_manager.active_count
        pending = self._download_manager.pending_count
        self._on_queue_changed(total, active, pending)

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
        logger.info("TubeGrab shutting down — cancelling all downloads")

        # Cancel all downloads through the manager
        self._download_manager.cancel_all()

        # Give active workers a moment to stop cleanly
        for worker in list(self._download_manager._workers.values()):
            if worker.isRunning():
                worker.quit()
                finished = worker.wait(5000)
                if not finished:
                    logger.warning("Worker did not stop in time; terminating")
                    worker.terminate()
                    worker.wait(2000)

        # Stop any in-flight metadata worker
        if self._metadata_worker is not None and self._metadata_worker.isRunning():
            self._metadata_worker.quit()
            self._metadata_worker.wait(3000)

        # Stop any in-flight playlist worker
        if self._playlist_worker is not None and self._playlist_worker.isRunning():
            self._playlist_worker.quit()
            self._playlist_worker.wait(3000)

        logger.info("All workers stopped — goodbye")
        super().closeEvent(event)
