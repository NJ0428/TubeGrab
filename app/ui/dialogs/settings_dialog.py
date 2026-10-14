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
)

from app.utils.config import Config


class SettingsDialog(QDialog):
    settings_changed = Signal()
    theme_changed = Signal(str)

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("Settings")
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
        self._path_edit.setPlaceholderText("Select download folder…")
        path_row.addWidget(self._path_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.setObjectName("iconButton")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._on_browse)
        path_row.addWidget(browse_btn)
        form.addRow(QLabel("Download path:"), path_row)

        # Default resolution
        self._resolution_combo = QComboBox()
        self._resolution_combo.addItems(
            ["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
        )
        form.addRow(QLabel("Default resolution:"), self._resolution_combo)

        # Default format
        self._format_combo = QComboBox()
        self._format_combo.addItems(["MP4", "WEBM", "MP3", "M4A"])
        form.addRow(QLabel("Default format:"), self._format_combo)

        # Max concurrent downloads
        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 10)
        form.addRow(QLabel("Max concurrent downloads:"), self._concurrent_spin)

        # Theme
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        form.addRow(QLabel("Theme:"), self._theme_combo)

        # Notify on complete
        self._notify_check = QCheckBox("Notify when download completes")
        form.addRow("", self._notify_check)

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
        theme_idx = self._theme_combo.findText(theme)
        if theme_idx >= 0:
            self._theme_combo.setCurrentIndex(theme_idx)

        self._notify_check.setChecked(
            bool(self._config.get("notify_on_complete"))
        )

    def _on_browse(self) -> None:
        current = self._path_edit.text() or str(Path.home() / "Downloads")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            current,
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._path_edit.setText(folder)

    def _on_accept(self) -> None:
        old_theme = (self._config.get("theme") or "dark").lower()

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
        new_theme = self._theme_combo.currentText().lower()
        self._config.set("theme", new_theme)
        self._config.set("notify_on_complete", self._notify_check.isChecked())
        self._config.save()

        self.settings_changed.emit()
        if new_theme != old_theme:
            self.theme_changed.emit(new_theme)

        self.accept()
