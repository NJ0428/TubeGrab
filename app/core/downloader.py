"""
Downloader — drives yt-dlp to perform a single download task.
"""

from __future__ import annotations

from typing import Callable

from app.models.download_task import DownloadTask
from app.utils.logger import get_logger
from app.utils.validators import sanitize_filename

logger = get_logger("core.downloader")


class Downloader:
    """Executes a DownloadTask using yt-dlp as a library.

    Args:
        ffmpeg_path: Optional explicit path to the ffmpeg executable.
                     When None, yt-dlp uses whatever is on PATH.
    """

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        self._ffmpeg_path = ffmpeg_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download(
        self,
        task: DownloadTask,
        progress_callback: Callable[[dict], None],
        cancel_check: Callable[[], bool],
    ) -> str:
        """Download the video described by *task*.

        Args:
            task:              The DownloadTask with all parameters.
            progress_callback: Called by yt-dlp with progress dicts.
            cancel_check:      Polled inside the progress hook; raising
                               DownloadError("Cancelled") aborts the download.

        Returns:
            Path to the final output file (str).

        Raises:
            yt_dlp.utils.DownloadError: On cancellation or yt-dlp error.
            Exception: On unexpected errors.
        """
        try:
            import yt_dlp  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "yt-dlp is not installed. Run: pip install yt-dlp"
            ) from exc

        fmt_string = self._build_format_string(task.resolution, task.format)
        sanitized_title = sanitize_filename(task.video_info.title)
        outtmpl = f"{task.save_path}/{sanitized_title}.%(ext)s"

        # We need a mutable container so the hook closure can store the path
        result_container: dict = {"filepath": ""}

        def _progress_hook(d: dict) -> None:
            # Poll cancellation first
            if cancel_check():
                raise yt_dlp.utils.DownloadError("Cancelled")

            status = d.get("status", "")
            if status == "finished":
                # yt-dlp gives us the filename when merging is done
                fp = d.get("filename") or d.get("info_dict", {}).get("filepath", "")
                if fp:
                    result_container["filepath"] = fp

            progress_callback(d)

        opts = self._build_opts(task, fmt_string, outtmpl, _progress_hook)

        logger.info(
            "Starting download — url=%s format_string=%r outtmpl=%r",
            task.video_info.url,
            fmt_string,
            outtmpl,
        )

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(task.video_info.url, download=True)

        # Try to recover the filepath from the info dict if hook didn't capture it
        final_path = result_container["filepath"]
        if not final_path and info:
            final_path = (
                info.get("filepath")
                or info.get("requested_downloads", [{}])[0].get("filepath", "")
            )
        if not final_path:
            # Fallback: construct a plausible path
            ext = task.format if task.format in ("mp3", "m4a") else task.format
            final_path = f"{task.save_path}/{sanitized_title}.{ext}"

        logger.info("Download complete: %s", final_path)
        return final_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_format_string(self, resolution: str, fmt: str) -> str:
        """Build the yt-dlp format selector string.

        Args:
            resolution: e.g. "Best", "1080p", "720p"
            fmt:        e.g. "mp4", "webm", "mp3", "m4a"

        Returns:
            A yt-dlp format selector string.
        """
        is_audio_only = fmt in ("mp3", "m4a")
        is_best = resolution.lower() == "best"

        if is_audio_only:
            return "bestaudio/best"

        if is_best:
            if fmt == "mp4":
                return "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            else:
                # webm or other video container
                return "bestvideo+bestaudio/best"

        # Specific resolution, e.g. "1080p" → 1080
        height_str = resolution.rstrip("p").strip()
        try:
            height = int(height_str)
        except ValueError:
            logger.warning(
                "Could not parse resolution %r, falling back to best", resolution
            )
            return "bestvideo+bestaudio/best"

        if fmt == "mp4":
            return (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={height}]+bestaudio"
                f"/best[height<={height}]"
            )
        else:
            return (
                f"bestvideo[height<={height}]+bestaudio"
                f"/best[height<={height}]"
            )

    def _build_opts(
        self,
        task: DownloadTask,
        fmt_string: str,
        outtmpl: str,
        progress_hook: Callable[[dict], None],
    ) -> dict:
        """Assemble the full yt-dlp options dict.

        Args:
            task:          The DownloadTask.
            fmt_string:    yt-dlp format selector.
            outtmpl:       Output template string.
            progress_hook: Hook function for progress events.

        Returns:
            dict of yt-dlp options.
        """
        is_audio_only = task.format in ("mp3", "m4a")

        opts: dict = {
            "format": fmt_string,
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
        }

        if self._ffmpeg_path:
            opts["ffmpeg_location"] = self._ffmpeg_path

        if is_audio_only:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": task.format,  # "mp3" or "m4a"
                    "preferredquality": "192",
                }
            ]
        else:
            opts["merge_output_format"] = task.format

        if task.subtitle_langs and task.subtitle_format:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = task.subtitle_langs
            opts["subtitlesformat"] = task.subtitle_format
            opts["writeautomaticsub"] = True  # allow auto-generated as fallback
            if task.subtitle_only:
                opts["skip_download"] = True
                opts.pop("merge_output_format", None)
            else:
                # Embed subtitles in video when the container supports it (mp4 only)
                if task.format == "mp4":
                    existing_pp = opts.get("postprocessors", [])
                    existing_pp.append(
                        {"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False}
                    )
                    opts["postprocessors"] = existing_pp

        return opts
