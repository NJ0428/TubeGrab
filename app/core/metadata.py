"""
MetadataFetcher — uses yt-dlp as a library to retrieve video metadata.
"""

from __future__ import annotations

from app.models.video import VideoInfo
from app.utils.logger import get_logger

logger = get_logger("core.metadata")


class MetadataFetcher:
    """Fetch video metadata from a URL using yt-dlp."""

    def get_ydl_opts(self) -> dict:
        """Return the base yt-dlp options dict used for metadata extraction.

        Returns:
            dict of yt-dlp options suitable for info extraction only.
        """
        return {
            "extract_flat": False,
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }

    def fetch(self, url: str) -> VideoInfo:
        """Fetch metadata for the given URL and return a VideoInfo object.

        Args:
            url: A YouTube (or other yt-dlp supported) video URL.

        Returns:
            A fully populated VideoInfo dataclass.

        Raises:
            ValueError: If the URL is invalid, the video is unavailable,
                        or any network/extraction error occurs.
        """
        try:
            import yt_dlp  # type: ignore[import]
        except ImportError as exc:
            raise ValueError(
                "yt-dlp is not installed. Run: pip install yt-dlp"
            ) from exc

        opts = self.get_ydl_opts()

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                logger.info("Extracting info for: %s", url)
                info: dict = ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            # Strip the yt-dlp prefix noise for a cleaner user-facing message
            raw = str(exc)
            # Common pattern: "ERROR: <actual message>"
            if "ERROR:" in raw:
                clean = raw.split("ERROR:", 1)[-1].strip()
            else:
                clean = raw
            logger.warning("yt-dlp extraction failed: %s", clean)
            raise ValueError(clean) from exc
        except Exception as exc:
            logger.error("Unexpected error during metadata fetch: %s", exc)
            raise ValueError(str(exc)) from exc

        if info is None:
            raise ValueError("No information returned for the given URL.")

        # --- Parse fields ---
        title: str = info.get("title") or "Unknown Title"
        channel: str = (
            info.get("uploader")
            or info.get("channel")
            or "Unknown"
        )
        duration: int = int(info.get("duration") or 0)
        thumbnail_url: str = info.get("thumbnail") or ""
        raw_formats: list[dict] = info.get("formats") or []

        # --- Derive available resolutions ---
        available_resolutions = _extract_resolutions(raw_formats)

        # --- Parse available subtitles ---
        subtitles_raw: dict = info.get("subtitles") or {}
        auto_captions_raw: dict = info.get("automatic_captions") or {}
        available_subtitles = _extract_subtitles(subtitles_raw, auto_captions_raw)

        video_info = VideoInfo(
            url=url,
            title=title,
            channel=channel,
            duration=duration,
            thumbnail_url=thumbnail_url,
            formats=raw_formats,
            available_resolutions=available_resolutions,
            available_subtitles=available_subtitles,
        )
        logger.info(
            "Metadata fetched — title=%r channel=%r duration=%d resolutions=%s",
            title,
            channel,
            duration,
            available_resolutions,
        )
        return video_info


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_LANG_NAMES: dict[str, str] = {
    "ko": "Korean",
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "it": "Italian",
}


def _lang_display_name(code: str) -> str:
    """Return a human-readable language name for *code*.

    Args:
        code: A BCP-47 language code, e.g. ``"ko"`` or ``"en"``.

    Returns:
        A human-readable name such as ``"Korean"``, falling back to the
        code itself capitalised when no mapping exists.
    """
    # Normalise: strip region tags for lookup (e.g. "en-US" → "en")
    base = code.split("-")[0].lower()
    return _LANG_NAMES.get(base, code.capitalize())


def _extract_subtitles(
    subtitles_raw: dict,
    auto_captions_raw: dict,
) -> dict[str, str]:
    """Merge manual subtitles and auto-captions into a single mapping.

    Language codes that appear *only* in ``auto_captions_raw`` receive an
    ``" (auto)"`` suffix in their display name.

    Args:
        subtitles_raw:    ``info["subtitles"]`` from yt-dlp.
        auto_captions_raw: ``info["automatic_captions"]`` from yt-dlp.

    Returns:
        A dict mapping language code to display name, e.g.
        ``{"ko": "Korean", "en": "English (auto)"}``.
    """
    result: dict[str, str] = {}

    for code in subtitles_raw:
        result[code] = _lang_display_name(code)

    for code in auto_captions_raw:
        if code not in result:
            result[code] = _lang_display_name(code) + " (auto)"

    return result


def _extract_resolutions(formats: list[dict]) -> list[str]:
    """Extract unique video heights from the formats list.

    Args:
        formats: Raw list of format dicts from yt-dlp.

    Returns:
        A list like ["Best", "1080p", "720p", "480p", "360p"] sorted
        descending, with "Best" always prepended.
    """
    heights: set[int] = set()
    for fmt in formats:
        height = fmt.get("height")
        if height and isinstance(height, (int, float)) and height > 0:
            heights.add(int(height))

    sorted_heights = sorted(heights, reverse=True)
    resolution_strings = [f"{h}p" for h in sorted_heights]
    return ["Best"] + resolution_strings
