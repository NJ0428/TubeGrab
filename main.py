"""
TubeGrab – Application Entry Point

Run with:
    python main.py
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.utils.config import Config
from app.utils.logger import get_logger
from app.ui.main_window import MainWindow

logger = get_logger("main")

_STYLES_DIR = Path(__file__).resolve().parent / "assets" / "styles"


def load_stylesheet(theme: str) -> str:
    """Read and return QSS for the given theme name."""
    qss_path = _STYLES_DIR / f"{theme}.qss"
    if qss_path.exists():
        try:
            return qss_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Could not read stylesheet %s: %s", qss_path, exc)
    else:
        logger.warning("Stylesheet not found: %s", qss_path)
    return ""


def main() -> int:
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("TubeGrab")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("TubeGrab")

    # Load config to determine initial theme
    config = Config()
    config.load()
    initial_theme = config.get("theme") or "dark"

    # Apply stylesheet before creating any widgets
    qss = load_stylesheet(initial_theme)
    if qss:
        app.setStyleSheet(qss)
        logger.info("Applied '%s' theme", initial_theme)

    # Create and show main window
    window = MainWindow(config=config)
    window.show()

    logger.info("TubeGrab started")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
