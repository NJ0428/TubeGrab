"""
HistoryManager — persists completed download history to ~/.tubegrab/history.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from app.models.history_entry import HistoryEntry
from app.utils.logger import get_logger

if TYPE_CHECKING:
    from app.models.download_task import DownloadTask

logger = get_logger("core.history")

_HISTORY_DIR = Path.home() / ".tubegrab"
_HISTORY_FILE = _HISTORY_DIR / "history.json"


class HistoryManager:
    """Manages persistence of download history to ~/.tubegrab/history.json."""

    MAX_ENTRIES: int = 500  # cap to avoid unbounded growth

    def __init__(self) -> None:
        self._path: Path = _HISTORY_FILE
        self._entries: list[HistoryEntry] = []

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load history from disk. Silently ignores missing or corrupt files."""
        try:
            if not self._path.exists():
                logger.debug("No history file found at %s", self._path)
                return
            with self._path.open("r", encoding="utf-8") as fh:
                raw: list[dict] = json.load(fh)
            entries: list[HistoryEntry] = []
            for item in raw:
                try:
                    entries.append(HistoryEntry.from_dict(item))
                except (KeyError, TypeError) as exc:
                    logger.warning("Skipping malformed history entry: %s", exc)
            self._entries = entries
            logger.debug("History loaded — %d entries from %s", len(self._entries), self._path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load history (%s); starting fresh", exc)
            self._entries = []

    def save(self) -> None:
        """Persist current history to disk."""
        try:
            _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            data = [entry.to_dict() for entry in self._entries]
            with self._path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            logger.debug("History saved — %d entries to %s", len(self._entries), self._path)
        except OSError as exc:
            logger.error("Failed to save history: %s", exc)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, entry: HistoryEntry) -> None:
        """Prepend entry (newest first), enforce MAX_ENTRIES cap, then save."""
        # Remove any existing entry with the same task_id to avoid duplicates
        self._entries = [e for e in self._entries if e.task_id != entry.task_id]
        self._entries.insert(0, entry)
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries = self._entries[: self.MAX_ENTRIES]
        self.save()
        logger.debug("History entry added — task_id=%s title=%r", entry.task_id, entry.title)

    def remove(self, task_id: str) -> None:
        """Remove entry by task_id and save."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.task_id != task_id]
        if len(self._entries) < before:
            self.save()
            logger.debug("History entry removed — task_id=%s", task_id)
        else:
            logger.warning("History remove — task_id not found: %s", task_id)

    def clear(self) -> None:
        """Remove all entries and save."""
        self._entries = []
        self.save()
        logger.info("History cleared")

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[HistoryEntry]:
        """Return entries where title or url contains query (case-insensitive)."""
        q = query.lower().strip()
        if not q:
            return list(self._entries)
        return [
            e for e in self._entries
            if q in e.title.lower() or q in e.url.lower()
        ]

    def filter_by_date(self, date_str: str) -> list[HistoryEntry]:
        """Return entries where completed_at starts with date_str (e.g. '2024-01-15')."""
        ds = date_str.strip()
        if not ds:
            return list(self._entries)
        return [e for e in self._entries if e.completed_at.startswith(ds)]

    @property
    def entries(self) -> list[HistoryEntry]:
        """Return a shallow copy of the full entry list."""
        return list(self._entries)

    # ------------------------------------------------------------------
    # Factory helper
    # ------------------------------------------------------------------

    @staticmethod
    def entry_from_task(task: "DownloadTask") -> HistoryEntry:
        """Build a HistoryEntry from a completed DownloadTask."""
        from datetime import datetime
        return HistoryEntry(
            task_id=task.task_id,
            url=task.video_info.url,
            title=task.video_info.title,
            channel=task.video_info.channel,
            resolution=task.resolution,
            format=task.format,
            save_path=task.save_path,
            output_file=task.output_file,
            file_size=task.total_bytes,
            completed_at=datetime.now().isoformat(timespec="seconds"),
        )
