"""
SubtitleDialog — lets the user configure subtitle download options.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.models.video import VideoInfo


# ---------------------------------------------------------------------------
# Fallback language list shown when no video metadata is available
# ---------------------------------------------------------------------------
_FALLBACK_LANGS: list[tuple[str, str]] = [
    ("en", "English"),
    ("ko", "Korean"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
]


class SubtitleDialog(QDialog):
    """Dialog for configuring subtitle language, format and download mode.

    Signals:
        subtitle_options_set: Emitted when the user confirms their selection.
            Arguments: (langs: list[str], fmt: str, subtitle_only: bool)
    """

    subtitle_options_set = Signal(list, str, bool)

    def __init__(
        self,
        video_info: VideoInfo | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._video_info = video_info
        self.setWindowTitle("Subtitle Options")
        self.setMinimumSize(480, 400)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # --- Header ---
        header_lbl = QLabel("Subtitle Options")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(14)
        header_lbl.setFont(header_font)
        main_layout.addWidget(header_lbl)

        # --- No-info notice (shown when subtitle data is unavailable) ---
        has_subtitles = bool(
            self._video_info is not None
            and self._video_info.available_subtitles
        )
        if not has_subtitles:
            notice_lbl = QLabel(
                "No subtitle information available. "
                "Languages will be requested as-is."
            )
            notice_lbl.setObjectName("infoMeta")
            notice_lbl.setWordWrap(True)
            main_layout.addWidget(notice_lbl)

        # --- Language section ---
        lang_section_lbl = QLabel("Select Languages:")
        lang_section_lbl.setObjectName("sectionLabel")
        main_layout.addWidget(lang_section_lbl)

        self._lang_list = QListWidget()
        self._lang_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
        )
        self._lang_list.setMinimumHeight(150)
        self._populate_lang_list(has_subtitles)
        main_layout.addWidget(self._lang_list)

        ctrl_note_lbl = QLabel("Hold Ctrl to select multiple languages")
        ctrl_note_lbl.setObjectName("infoMeta")
        main_layout.addWidget(ctrl_note_lbl)

        # --- Format section ---
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(10)

        fmt_lbl = QLabel("Subtitle Format:")
        fmt_lbl.setFixedWidth(120)
        fmt_row.addWidget(fmt_lbl)

        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["SRT", "VTT"])
        self._fmt_combo.setFixedWidth(100)
        self._fmt_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        fmt_row.addWidget(self._fmt_combo)

        fmt_row.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        main_layout.addLayout(fmt_row)

        # --- Options section ---
        self._auto_sub_chk = QCheckBox("Include auto-generated subtitles")
        self._auto_sub_chk.setChecked(True)
        main_layout.addWidget(self._auto_sub_chk)

        self._subtitle_only_chk = QCheckBox("Download subtitles only (no video)")
        self._subtitle_only_chk.setChecked(False)
        main_layout.addWidget(self._subtitle_only_chk)

        main_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- OK / Cancel buttons ---
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        main_layout.addWidget(btn_box)

    def _populate_lang_list(self, has_subtitles: bool) -> None:
        """Fill the language list from video metadata or the fallback list."""
        if has_subtitles and self._video_info is not None:
            entries = list(self._video_info.available_subtitles.items())
        else:
            entries = _FALLBACK_LANGS

        for code, name in entries:
            item = QListWidgetItem(f"{name} [{code}]")
            item.setData(Qt.ItemDataRole.UserRole, code)
            self._lang_list.addItem(item)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_selected_langs(self) -> list[str]:
        """Return a list of selected language codes.

        Returns:
            A (possibly empty) list of BCP-47 language code strings.
        """
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self._lang_list.selectedItems()
        ]

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_ok(self) -> None:
        """Emit subtitle_options_set and close the dialog."""
        langs = self.get_selected_langs()
        fmt = self._fmt_combo.currentText().lower()  # "srt" or "vtt"
        subtitle_only = self._subtitle_only_chk.isChecked()
        self.subtitle_options_set.emit(langs, fmt, subtitle_only)
        self.accept()
