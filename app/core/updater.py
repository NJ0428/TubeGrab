"""
yt-dlp version checker and updater for TubeGrab.
"""

import subprocess
import sys
from dataclasses import dataclass

from app.utils.logger import get_logger

logger = get_logger("core.updater")


@dataclass
class UpdateResult:
    success: bool
    old_version: str
    new_version: str
    message: str    # human-readable summary
    updated: bool   # True if version actually changed


def get_ytdlp_version() -> str:
    """Return the installed yt-dlp version string, or 'unknown' on failure."""
    try:
        import yt_dlp
        return yt_dlp.version.__version__
    except Exception:
        return "unknown"


def check_latest_version() -> str:
    """Fetch the latest yt-dlp version from PyPI JSON API.

    Returns the latest version string, or empty string on failure.
    Uses httpx for the request with a 10s timeout.
    """
    try:
        import httpx
        resp = httpx.get("https://pypi.org/pypi/yt-dlp/json", timeout=10.0)
        resp.raise_for_status()
        return resp.json()["info"]["version"]
    except Exception as exc:
        logger.warning("Failed to fetch latest yt-dlp version: %s", exc)
        return ""


def update_ytdlp() -> UpdateResult:
    """Run pip install --upgrade yt-dlp in a subprocess.

    Returns UpdateResult with before/after version info.
    """
    old_version = get_ytdlp_version()
    logger.info("Starting yt-dlp update (current: %s)", old_version)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            msg = result.stderr.strip() or result.stdout.strip() or "pip exited with error"
            logger.error("yt-dlp update failed: %s", msg)
            return UpdateResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=f"Update failed: {msg[:200]}",
                updated=False,
            )
        # Re-import to get new version — need to reload the module
        import importlib
        try:
            import yt_dlp.version
            importlib.reload(yt_dlp.version)
            import yt_dlp
            importlib.reload(yt_dlp)
        except Exception:
            pass
        new_version = get_ytdlp_version()
        updated = new_version != old_version
        if updated:
            msg = f"Updated yt-dlp: {old_version} \u2192 {new_version}"
        else:
            msg = f"yt-dlp is already up to date ({new_version})"
        logger.info(msg)
        return UpdateResult(
            success=True,
            old_version=old_version,
            new_version=new_version,
            message=msg,
            updated=updated,
        )
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp update timed out")
        return UpdateResult(
            success=False,
            old_version=old_version,
            new_version=old_version,
            message="Update timed out after 120 seconds.",
            updated=False,
        )
    except Exception as exc:
        logger.error("Unexpected error during yt-dlp update: %s", exc)
        return UpdateResult(
            success=False,
            old_version=old_version,
            new_version=old_version,
            message=str(exc),
            updated=False,
        )
