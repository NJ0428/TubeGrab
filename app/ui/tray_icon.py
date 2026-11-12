"""
TrayIcon — system tray icon, context menu, badge, and notifications for TubeGrab.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    """Manages the system tray icon, context menu, badge overlays, and toast notifications.

    Signals:
        show_window_requested: Emitted when the user clicks "Show Window" or
                               single/double-clicks the tray icon.
        exit_requested:        Emitted when the user clicks "Exit".
        pause_requested:       Emitted when the user clicks "Pause Downloads".
        resume_requested:      Emitted when the user clicks "Resume Downloads".
    """

    show_window_requested: Signal = Signal()
    exit_requested: Signal = Signal()
    pause_requested: Signal = Signal()
    resume_requested: Signal = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._base_pixmap: QPixmap = self._make_base_pixmap()
        self.setIcon(QIcon(self._base_pixmap))
        self._build_menu()
        self.setToolTip("TubeGrab")
        self.activated.connect(self._on_activated)

    # ------------------------------------------------------------------
    # Icon helpers
    # ------------------------------------------------------------------

    def _make_base_pixmap(self) -> QPixmap:
        """Create and return the 32×32 base pixmap (red background, white 'TG')."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor("#e94560"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        painter.drawText(pixmap.rect(), 0x84, "TG")  # Qt::AlignHCenter | Qt::AlignVCenter

        painter.end()
        return pixmap

    def _build_base_icon(self) -> QIcon:
        """Return a fresh QIcon from the base pixmap."""
        return QIcon(self._make_base_pixmap())

    def _build_badge_icon(self, count: int) -> QIcon:
        """Return a QIcon with a small badge showing *count* (capped at '9+')."""
        pixmap = self._make_base_pixmap().copy()

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw orange badge circle in the bottom-right corner
        badge_size = 12
        badge_x = pixmap.width() - badge_size
        badge_y = pixmap.height() - badge_size

        painter.setBrush(QColor("#f5a623"))
        painter.setPen(QColor("white"))
        painter.drawEllipse(badge_x, badge_y, badge_size, badge_size)

        # Draw count text inside the badge
        badge_font = QFont()
        badge_font.setPointSize(8)
        badge_font.setBold(True)
        painter.setFont(badge_font)
        painter.setPen(QColor("white"))

        label = str(count) if count <= 9 else "9+"
        from PySide6.QtCore import QRect
        badge_rect = QRect(badge_x, badge_y, badge_size, badge_size)
        painter.drawText(badge_rect, 0x84, label)  # AlignHCenter | AlignVCenter

        painter.end()
        return QIcon(pixmap)

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> None:
        """Create and attach the tray context menu."""
        self._menu = QMenu()

        self._show_action = QAction("Show Window")
        self._show_action.triggered.connect(self.show_window_requested.emit)
        self._menu.addAction(self._show_action)

        self._menu.addSeparator()

        self._pause_action = QAction("Pause Downloads")
        self._pause_action.triggered.connect(self.pause_requested.emit)
        self._menu.addAction(self._pause_action)

        self._resume_action = QAction("Resume Downloads")
        self._resume_action.triggered.connect(self.resume_requested.emit)
        self._resume_action.setVisible(False)
        self._menu.addAction(self._resume_action)

        self._menu.addSeparator()

        exit_action = QAction("Exit")
        exit_action.triggered.connect(self.exit_requested.emit)
        self._menu.addAction(exit_action)

        self.setContextMenu(self._menu)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_badge(self, active: int, paused: bool = False) -> None:
        """Update the tray icon badge and tooltip to reflect *active* downloads.

        Args:
            active: Number of currently active (running) downloads.
            paused: Whether the download queue is currently paused.
        """
        if active > 0:
            self.setIcon(self._build_badge_icon(active))
            self.setToolTip(f"TubeGrab — {active} download(s) active")
        else:
            self.setIcon(self._build_base_icon())
            self.setToolTip("TubeGrab")

        if paused:
            self._pause_action.setVisible(False)
            self._resume_action.setVisible(True)
        else:
            self._pause_action.setVisible(True)
            self._resume_action.setVisible(False)

    def show_download_notification(self, title: str) -> None:
        """Show a tray notification for a completed download.

        Args:
            title: The video title (will be truncated to 60 characters).
        """
        self.showMessage(
            "TubeGrab",
            f"Download complete: {title[:60]}",
            QSystemTrayIcon.MessageIcon.Information,
            4000,
        )

    def show_error_notification(self, title: str, msg: str) -> None:
        """Show a tray notification for a failed download.

        Args:
            title: The video title (will be truncated to 40 characters).
            msg:   The error message (will be truncated to 60 characters).
        """
        self.showMessage(
            "TubeGrab",
            f"Download failed: {title[:40]}\n{msg[:60]}",
            QSystemTrayIcon.MessageIcon.Warning,
            5000,
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Restore the window when the user single- or double-clicks the tray icon."""
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.show_window_requested.emit()
