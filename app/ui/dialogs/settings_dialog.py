"""
SettingsDialog — application preferences editor.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)

from app.utils.config import Config
from app.utils.i18n import tr


class SettingsDialog(QDialog):
    settings_changed = Signal()
    theme_changed = Signal(str)
    language_changed = Signal(str)

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle(tr("Settings"))
        self.setMinimumWidth(420)
        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 16, 20, 16)

        form = QFormLayout()
        form.setSpacing(10)
        form.setContentsMargins(0, 0, 0, 0)

        # Download path
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self._path_edit = QLineEdit()
        self._path_edit.setObjectName("savePathInput")
        self._path_edit.setPlaceholderText(tr("Select download folder…"))
        path_row.addWidget(self._path_edit)
        browse_btn = QPushButton(tr("Browse…"))
        browse_btn.setObjectName("iconButton")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(browse_btn)
        form.addRow(QLabel(tr("Download path:")), path_row)

        # Default resolution
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(
            ["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
        )
        form.addRow(QLabel(tr("Default resolution:")), self._resolution_combo)

        # Default format
        self._format_combo = QComboBox()
        self._format_combo.addItems(["MP4", "WEBM", "MP3", "M4A"])
        form.addRow(QLabel(tr("Default format:")), self._format_combo)

        # Max concurrent downloads
        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 10)
        form.addRow(QLabel(tr("Max concurrent downloads:")), self._concurrent_spin)

        # Theme
        self._theme_combo = QComboBox()
        self._theme_combo.addItems([tr("Dark"), tr("Light")])
        form.addRow(QLabel(tr("Theme:")), self._theme_combo)

        # Language
        self._language_combo = QComboBox()
        self._language_combo.addItems(["English", "한국어"])
        form.addRow(QLabel(tr("Language:")), self._language_combo)

        # Notify on complete
        self._notify_check = QCheckBox(tr("Notify when download completes"))
        form.addRow("", self._notify_check)

        # Clipboard detection
        self._clipboard_check = QCheckBox(
            tr("Auto-detect YouTube URLs from clipboard on focus")
        )
        form.addRow("", self._clipboard_check)

        # Clipboard auto-fill mode
        self._autofill_check = QCheckBox(tr("Auto-fill silently (no confirmation banner)"))
        form.addRow("", self._autofill_check)

        # Minimize to tray
        self._tray_check = QCheckBox(
            tr("Minimize to tray on close (instead of quitting)")
        )
        form.addRow("", self._tray_check)

        # Tray notifications
        self._tray_notify_check = QCheckBox(
            tr("Show tray notification on download complete")
        )
        form.addRow("", self._tray_notify_check)

        # ── Filename Template ─────────────────────────────────────────
        template_lbl = QLabel(tr("── Filename Template ──"))
        template_lbl.setObjectName("sectionLabel")
        form.addRow(template_lbl)

        # Template input + preview + error stacked in a column
        template_row = QVBoxLayout()
        template_row.setSpacing(4)

        self._template_edit = QLineEdit()
        self._template_edit.setPlaceholderText("{title}")
        self._template_edit.setObjectName("templateInput")
        self._template_edit.textChanged.connect(self._on_template_changed)
        template_row.addWidget(self._template_edit)

        self._template_preview_lbl = QLabel("")
        self._template_preview_lbl.setObjectName("infoMeta")
        template_row.addWidget(self._template_preview_lbl)

        self._template_error_lbl = QLabel("")
        self._template_error_lbl.setObjectName("urlValidInvalid")
        template_row.addWidget(self._template_error_lbl)

        template_widget = QWidget()
        template_widget.setLayout(template_row)
        form.addRow(QLabel(tr("Template:")), template_widget)

        # Quick-insert variable buttons
        hint_row = QHBoxLayout()
        hint_row.setSpacing(4)
        hint_lbl = QLabel(tr("Insert:"))
        hint_lbl.setObjectName("infoMeta")
        hint_row.addWidget(hint_lbl)
        for var in ("{title}", "{channel}", "{resolution}", "{date}", "{ext}"):
            btn = QPushButton(var)
            btn.setObjectName("clearBtn")
            btn.setFixedHeight(22)
            btn.clicked.connect(
                lambda checked=False, v=var: self._insert_template_var(v)
            )
            hint_row.addWidget(btn)
        hint_row.addStretch(1)
        hint_widget = QWidget()
        hint_widget.setLayout(hint_row)
        form.addRow("", hint_widget)

        # ── Speed Limit ───────────────────────────────────────────────
        speed_lbl = QLabel(tr("── Speed Limit ──"))
        speed_lbl.setObjectName("sectionLabel")
        form.addRow(speed_lbl)

        self._speed_limit_check = QCheckBox(tr("Limit download speed"))
        self._speed_limit_check.toggled.connect(self._on_speed_limit_toggled)
        form.addRow("", self._speed_limit_check)

        speed_row = QHBoxLayout()
        speed_row.setSpacing(6)
        self._speed_spin = QDoubleSpinBox()
        self._speed_spin.setRange(0.1, 99999.0)
        self._speed_spin.setDecimals(1)
        self._speed_spin.setSingleStep(1.0)
        self._speed_spin.setFixedWidth(100)
        speed_row.addWidget(self._speed_spin)
        self._speed_unit_combo = QComboBox()
        self._speed_unit_combo.addItems(["KB/s", "MB/s"])
        self._speed_unit_combo.setFixedWidth(70)
        self._speed_unit_combo.currentIndexChanged.connect(self._on_speed_unit_changed)
        speed_row.addWidget(self._speed_unit_combo)
        speed_row.addStretch(1)
        self._speed_row_widget = QWidget()
        self._speed_row_widget.setLayout(speed_row)
        form.addRow(QLabel(tr("Max speed:")), self._speed_row_widget)

        # ── yt-dlp ────────────────────────────────────────────────────
        ytdlp_lbl = QLabel(tr("── yt-dlp ──"))
        ytdlp_lbl.setObjectName("sectionLabel")
        form.addRow(ytdlp_lbl)

        # Current version display
        self._ytdlp_version_lbl = QLabel("\u2026")
        self._ytdlp_version_lbl.setObjectName("infoMeta")
        form.addRow(QLabel(tr("Installed version:")), self._ytdlp_version_lbl)

        # Auto-update checkbox
        self._auto_update_check = QCheckBox(tr("Automatically update yt-dlp on startup"))
        form.addRow("", self._auto_update_check)

        # Manual update button row
        update_row = QHBoxLayout()
        update_row.setSpacing(8)
        self._update_btn = QPushButton(tr("Update Now"))
        self._update_btn.setObjectName("fetchButton")
        self._update_btn.setFixedWidth(120)
        self._update_btn.clicked.connect(self._on_update_now)
        update_row.addWidget(self._update_btn)
        self._update_status_lbl = QLabel("")
        self._update_status_lbl.setObjectName("infoMeta")
        update_row.addWidget(self._update_status_lbl)
        update_row.addStretch(1)
        update_widget = QWidget()
        update_widget.setLayout(update_row)
        form.addRow("", update_widget)

        root.addLayout(form)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _load_values(self) -> None:
        self._path_edit.setText(
            self._config.get("download_path") or str(Path.home() / "Downloads")
        )

        res = (self._config.get("default_resolution") or "best").lower()
        res_map = {
            "best": "Best", "2160p": "2160p", "1440p": "1440p",
            "1080p": "1080p", "720p": "720p", "480p": "480p", "360p": "360p",
        }
        idx = self._resolution_combo.findText(res_map.get(res, "Best"))
        if idx >= 0:
            self._resolution_combo.setCurrentIndex(idx)

        fmt = (self._config.get("default_format") or "mp4").upper()
        fmt_idx = self._format_combo.findText(fmt)
        if fmt_idx >= 0:
            self._format_combo.setCurrentIndex(fmt_idx)

        self._concurrent_spin.setValue(
            int(self._config.get("max_concurrent_downloads") or 3)
        )

        theme = (self._config.get("theme") or "dark").capitalize()
        theme_idx = self._theme_combo.findText(tr(theme))
        if theme_idx >= 0:
            self._theme_combo.setCurrentIndex(theme_idx)

        # Language
        lang = self._config.get("language") or "en"
        lang_map = {"en": "English", "ko": "한국어"}
        lang_idx = self._language_combo.findText(lang_map.get(lang, "English"))
        if lang_idx >= 0:
            self._language_combo.setCurrentIndex(lang_idx)

        self._notify_check.setChecked(
            bool(self._config.get("notify_on_complete"))
        )
        self._clipboard_check.setChecked(bool(self._config.get("clipboard_detection")))
        self._autofill_check.setChecked(bool(self._config.get("clipboard_auto_fill")))
        self._tray_check.setChecked(bool(self._config.get("minimize_to_tray")))
        self._tray_notify_check.setChecked(bool(self._config.get("tray_notifications")))

        self._template_edit.setText(
            self._config.get("filename_template") or ""
        )
        self._on_template_changed(self._template_edit.text())

        # Speed limit
        speed_enabled = bool(self._config.get("speed_limit_enabled"))
        speed_kbps = int(self._config.get("speed_limit_kbps") or 1024)
        self._speed_limit_check.setChecked(speed_enabled)
        # Display in MB/s when >= 1024 KB/s, otherwise KB/s
        if speed_kbps >= 1024 and speed_kbps % 1024 == 0:
            self._speed_unit_combo.setCurrentIndex(1)  # MB/s
            self._speed_spin.setValue(speed_kbps / 1024.0)
        else:
            self._speed_unit_combo.setCurrentIndex(0)  # KB/s
            self._speed_spin.setValue(float(speed_kbps))
        self._on_speed_limit_toggled(speed_enabled)

        from app.core.updater import get_ytdlp_version
        self._ytdlp_version_lbl.setText(get_ytdlp_version())
        self._auto_update_check.setChecked(bool(self._config.get("auto_update_ytdlp")))

    def _on_template_changed(self, text: str) -> None:
        """Update preview and error labels whenever the template text changes."""
        from app.utils.filename_template import (
            DEFAULT_TEMPLATE,
            render_template,
            validate_template,
        )

        template = text.strip() or DEFAULT_TEMPLATE
        is_valid, err = validate_template(template)
        if not is_valid:
            self._template_error_lbl.setText(err)
            self._template_preview_lbl.setText("")
        else:
            self._template_error_lbl.setText("")
            preview = render_template(
                template=template,
                title="My Awesome Video",
                channel="Some Channel",
                resolution="1080p",
                ext="mp4",
                task_id="abcd1234",
            )
            self._template_preview_lbl.setText(tr("Preview: {}").format(f"{preview}.mp4"))

    def _insert_template_var(self, var: str) -> None:
        """Insert *var* at the current cursor position in the template input."""
        cursor_pos = self._template_edit.cursorPosition()
        current = self._template_edit.text()
        new_text = current[:cursor_pos] + var + current[cursor_pos:]
        self._template_edit.setText(new_text)
        self._template_edit.setCursorPosition(cursor_pos + len(var))

    def _on_speed_limit_toggled(self, enabled: bool) -> None:
        """Enable or disable the speed input row based on the toggle."""
        self._speed_row_widget.setEnabled(enabled)

    def _on_speed_unit_changed(self, index: int) -> None:
        """Convert displayed value when user switches between KB/s and MB/s."""
        current = self._speed_spin.value()
        if index == 1:  # switched to MB/s
            self._speed_spin.setRange(0.1, 99999.0)
            self._speed_spin.setValue(max(0.1, current / 1024.0))
        else:  # switched to KB/s
            self._speed_spin.setRange(1.0, 999999.0)
            self._speed_spin.setValue(max(1.0, current * 1024.0))

    def _on_browse(self) -> None:
        current = self._path_edit.text() or str(Path.home() / "Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("Select Download Folder"),
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._path_edit.setText(folder)

    def _on_accept(self) -> None:
        old_theme = (self._config.get("theme") or "dark").lower()
        old_lang = self._config.get("language") or "en"

        self._config.set("download_path", self._path_edit.text().strip())
        self._config.set(
            "default_resolution",
            self._resolution_combo.currentText().lower(),
        )
        self._config.set(
            "default_format",
            self._format_combo.currentText().lower(),
        )
        self._config.set("max_concurrent_downloads", self._concurrent_spin.value())

        # Theme — resolve display text back to internal value
        theme_display = self._theme_combo.currentText()
        theme_reverse = {tr("Dark"): "dark", tr("Light"): "light"}
        new_theme = theme_reverse.get(theme_display, theme_display.lower())
        self._config.set("theme", new_theme)

        # Language
        lang_display = self._language_combo.currentText()
        lang_reverse = {"English": "en", "한국어": "ko"}
        new_lang = lang_reverse.get(lang_display, "en")
        self._config.set("language", new_lang)

        self._config.set("notify_on_complete", self._notify_check.isChecked())
        self._config.set("clipboard_detection", self._clipboard_check.isChecked())
        self._config.set("clipboard_auto_fill", self._autofill_check.isChecked())
        self._config.set("minimize_to_tray", self._tray_check.isChecked())
        self._config.set("tray_notifications", self._tray_notify_check.isChecked())
        self._config.set("filename_template", self._template_edit.text().strip())
        self._config.set("auto_update_ytdlp", self._auto_update_check.isChecked())

        # Speed limit
        self._config.set("speed_limit_enabled", self._speed_limit_check.isChecked())
        raw_value = self._speed_spin.value()
        if self._speed_unit_combo.currentText() == "MB/s":
            kbps = int(raw_value * 1024)
        else:
            kbps = int(raw_value)
        self._config.set("speed_limit_kbps", max(1, kbps))

        self._config.save()

        self.settings_changed.emit()
        if new_theme != old_theme:
            self.theme_changed.emit(new_theme)
        if new_lang != old_lang:
            self.language_changed.emit(new_lang)

        self.accept()

    def _on_update_now(self) -> None:
        """Start a manual yt-dlp update in the background."""
        from app.workers.update_worker import UpdateWorker
        self._update_btn.setEnabled(False)
        self._update_status_lbl.setText(tr("Updating…"))
        worker = UpdateWorker(auto_update=True, parent=self)
        worker.update_finished.connect(self._on_update_result)
        worker.error.connect(lambda msg: self._on_update_result_error(msg))
        # Keep reference to avoid GC
        self._update_worker = worker
        worker.start()

    def _on_update_result(self, result: object) -> None:
        """Handle the UpdateResult emitted by UpdateWorker."""
        from app.core.updater import UpdateResult
        r: UpdateResult = result  # type: ignore[assignment]
        self._update_btn.setEnabled(True)
        if r.success:
            self._update_status_lbl.setText(r.message)
            self._ytdlp_version_lbl.setText(r.new_version)
        else:
            self._update_status_lbl.setText(tr("Failed: {}").format(r.message[:80]))

    def _on_update_result_error(self, msg: str) -> None:
        """Handle unexpected worker errors."""
        self._update_btn.setEnabled(True)
        self._update_status_lbl.setText(tr("Error (settings): {}").format(msg[:80]))
