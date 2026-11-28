"""
Windows startup registry management for TubeGrab.

Registers / unregisters TubeGrab in
  HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
so that it launches automatically when the user logs in.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("core.startup")

_APP_NAME = "TubeGrab"
_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _build_command(minimized: bool) -> str:
    """Return the command string to store in the registry value."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-bundled .exe
        cmd = f'"{sys.executable}"'
    else:
        # Running as a plain Python script
        script = str(Path(__file__).resolve().parents[2] / "main.py")
        cmd = f'"{sys.executable}" "{script}"'
    if minimized:
        cmd += " --minimized"
    return cmd


def is_registered() -> bool:
    """Return True if TubeGrab has an entry in the Windows startup registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, _APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception as exc:
        logger.warning("Could not read startup registry: %s", exc)
        return False


def register(minimized: bool = False) -> bool:
    """Write TubeGrab into the Windows startup registry. Returns True on success."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        cmd = _build_command(minimized)
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        logger.info("Startup registered: %s", cmd)
        return True
    except Exception as exc:
        logger.error("Failed to register startup: %s", exc)
        return False


def unregister() -> bool:
    """Remove TubeGrab from the Windows startup registry. Returns True on success."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, _APP_NAME)
            logger.info("Startup unregistered")
        except FileNotFoundError:
            pass  # Already absent — not an error
        finally:
            winreg.CloseKey(key)
        return True
    except Exception as exc:
        logger.error("Failed to unregister startup: %s", exc)
        return False
