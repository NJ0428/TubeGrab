"""
ProgressCardWidget — compact status summary bar for the download queue.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


class ProgressCardWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(20)

        self._total_lbl = QLabel("Total: 0")
        self._total_lbl.setObjectName("infoMeta")
        layout.addWidget(self._total_lbl)

        self._active_lbl = QLabel("Active: 0")
        self._active_lbl.setObjectName("infoMeta")
        layout.addWidget(self._active_lbl)

        self._completed_lbl = QLabel("Completed: 0")
        self._completed_lbl.setObjectName("infoMeta")
        layout.addWidget(self._completed_lbl)

        layout.addStretch(1)

    def update_stats(self, total: int, active: int, completed: int) -> None:
        """Refresh all counters."""
        self._total_lbl.setText(f"Total: {total}")
        self._active_lbl.setText(f"Active: {active}")
        self._completed_lbl.setText(f"Completed: {completed}")
