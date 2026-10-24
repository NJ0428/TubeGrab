"""
PlaylistFetcher — uses yt-dlp to retrieve playlist metadata.
"""

from __future__ import annotations

from typing import Callable

from app.models.playlist import PlaylistEntry, PlaylistInfo
from app.utils.logger import get_logger

logger = get_logger("core.playlist")


class PlaylistFetcher:
    """Fetch playlist metadata from a URL using yt-dlp."""

    def fetch(
        self,
        url: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> PlaylistInfo:
        """Fetch metadata for the given playlist URL and return a PlaylistInfo object.

        Args:
            url: A YouTube playlist URL.
            progress_callback: Optional callable(current, total) called after each
                               entry is processed.

        Returns:
            A fully populated PlaylistInfo dataclass.

        Raises:
            ValueError: If the URL is invalid, the playlist is unavailable,
                        or any network/extraction error occurs.
        """
        try:
            import yt_dlp  # type: ignore[import]
        except ImportError as exc:
            raise ValueError(
                "yt-dlp is not installed. Run: pip install yt-dlp"
            ) from exc

        opts = {
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                logger.info("Extracting playlist info for: %s", url)
                info: dict = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            raw = str(exc)
            if "ERROR:" in raw:
                clean = raw.split("ERROR:", 1)[-1].strip()
            else:
                clean = raw
            logger.warning("yt-dlp playlist extraction failed: %s", clean)
            raise ValueError(clean) from exc
        except Exception as exc:
            logger.error("Unexpected error during playlist fetch: %s", exc)
            raise ValueError(str(exc)) from exc

        if info is None:
            raise ValueError("No information returned for the given URL.")

        # Validate it is a playlist
        if info.get("_type") != "playlist" and info.get("entries") is None:
            raise ValueError("The URL does not appear to be a playlist.")

        title: str = info.get("title") or "Unknown Playlist"
        channel: str = (
            info.get("uploader")
            or info.get("channel")
            or "Unknown"
        )

        raw_entries: list[dict] = info.get("entries") or []
        # Filter out None entries
        raw_entries = [e for e in raw_entries if e is not None]
        total = len(raw_entries)

        entries: list[PlaylistEntry] = []
        for idx, entry in enumerate(raw_entries, start=1):
            entry_url = (
                entry.get("url")
                or entry.get("webpage_url")
                or (f"https://www.youtube.com/watch?v={entry['id']}" if entry.get("id") else "")
            )
            entry_title: str = entry.get("title") or f"Video {idx}"
            duration: int = int(entry.get("duration") or 0)

            # Resolve thumbnail URL
            thumbnail_url: str = entry.get("thumbnail") or ""
            if not thumbnail_url:
                thumbnails = entry.get("thumbnails")
                if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                    thumbnail_url = thumbnails[-1].get("url", "") or ""

            entries.append(
                PlaylistEntry(
                    index=idx,
                    url=entry_url,
                    title=entry_title,
                    duration=duration,
                    thumbnail_url=thumbnail_url,
                )
            )

            if progress_callback is not None:
                progress_callback(idx, total)

        logger.info(
            "Playlist fetched — title=%r channel=%r entries=%d",
            title,
            channel,
            len(entries),
        )

        return PlaylistInfo(
            url=url,
            title=title,
            channel=channel,
            entries=entries,
        )
