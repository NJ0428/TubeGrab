"""
ProgressCardWidget — compact status summary bar for the download queue.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.utils.i18n import tr


class ProgressCardWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._total = 0
        self._active = 0
        self._completed = 0
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(20)

        self._total_lbl = QLabel(tr("Total: {}").format(0))
        self._total_lbl.setObjectName("infoMeta")
        layout.addWidget(self._total_lbl)

        self._active_lbl = QLabel(tr("Active: {}").format(0))
        self._active_lbl.setObjectName("infoMeta")
        layout.addWidget(self._active_lbl)

        self._completed_lbl = QLabel(tr("Completed: {}").format(0))
        self._completed_lbl.setObjectName("infoMeta")
        layout.addWidget(self._completed_lbl)

        layout.addStretch(1)

    def update_stats(self, total: int, active: int, completed: int) -> None:
        """Refresh all counters."""
        self._total = total
        self._active = active
        self._completed = completed
        self._total_lbl.setText(tr("Total: {}").format(total))
        self._active_lbl.setText(tr("Active: {}").format(active))
        self._completed_lbl.setText(tr("Completed: {}").format(completed))

    def retranslate_ui(self) -> None:
        """Update all translatable text for the active language."""
        self._total_lbl.setText(tr("Total: {}").format(self._total))
        self._active_lbl.setText(tr("Active: {}").format(self._active))
        self._completed_lbl.setText(tr("Completed: {}").format(self._completed))
