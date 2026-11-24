"""
Post-download countdown dialog for system actions (shutdown / sleep).
"""

from __future__ import annotations

import subprocess
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.utils.i18n import tr
from app.utils.logger import get_logger

logger = get_logger("ui.post_complete_dialog")

_COUNTDOWN_SECS = 30


class PostCompleteDialog(QDialog):
    """
    Modal countdown dialog shown before executing a post-download system action.

    Shows a *_COUNTDOWN_SECS*-second countdown and a Cancel button.
    When the countdown expires the requested action is executed.
    """

    def __init__(self, action: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        assert action in ("shutdown", "sleep"), f"Unknown action: {action!r}"
        self._action = action
        self._remaining = _COUNTDOWN_SECS

        self.setWindowTitle(tr("All Downloads Complete"))
        self.setMinimumWidth(380)
        self.setModal(True)
        # Prevent accidentally closing via the window's X button without cancelling
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )

        self._build_ui()

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        self._msg_lbl = QLabel()
        self._msg_lbl.setWordWrap(True)
        self._msg_lbl.setObjectName("infoMeta")
        layout.addWidget(self._msg_lbl)

        self._countdown_lbl = QLabel()
        self._countdown_lbl.setObjectName("sectionLabel")
        layout.addWidget(self._countdown_lbl)

        hint_lbl = QLabel(tr("Click Cancel to abort."))
        hint_lbl.setObjectName("infoMeta")
        layout.addWidget(hint_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setObjectName("iconButton")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._refresh_countdown_label()

        if self._action == "shutdown":
            self._msg_lbl.setText(tr("All downloads have finished.") + "\n" + tr("Shutdown PC") + "…")
        else:
            self._msg_lbl.setText(tr("All downloads have finished.") + "\n" + tr("Sleep") + "…")

    def _refresh_countdown_label(self) -> None:
        if self._action == "shutdown":
            self._countdown_lbl.setText(
                tr("PC will shut down in {} seconds.").format(self._remaining)
            )
        else:
            self._countdown_lbl.setText(
                tr("PC will sleep in {} seconds.").format(self._remaining)
            )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            self.accept()
            self._execute_action()
        else:
            self._refresh_countdown_label()

    def _on_cancel(self) -> None:
        self._timer.stop()
        logger.info("Post-complete action cancelled by user")
        self.reject()

    # ------------------------------------------------------------------
    # System action
    # ------------------------------------------------------------------

    def _execute_action(self) -> None:
        logger.info("Executing post-complete action: %s", self._action)
        try:
            if self._action == "shutdown":
                if sys.platform == "win32":
                    subprocess.Popen(["shutdown", "/s", "/t", "0"])
                elif sys.platform == "darwin":
                    subprocess.Popen(
                        ["osascript", "-e", 'tell application "System Events" to shut down']
                    )
                else:
                    subprocess.Popen(["systemctl", "poweroff"])
            elif self._action == "sleep":
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
                    )
                elif sys.platform == "darwin":
                    subprocess.Popen(
                        ["osascript", "-e", 'tell application "System Events" to sleep']
                    )
                else:
                    subprocess.Popen(["systemctl", "suspend"])
        except OSError as exc:
            logger.error("Failed to execute post-complete action %s: %s", self._action, exc)
