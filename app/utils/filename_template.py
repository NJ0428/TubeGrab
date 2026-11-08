"""
Filename template engine for TubeGrab.

Provides variable substitution for output filenames with sanitization.
"""

from __future__ import annotations

import string

from app.utils.validators import sanitize_filename

DEFAULT_TEMPLATE: str = "{title}"

AVAILABLE_VARIABLES: list[tuple[str, str]] = [
    ("{title}", "Video title"),
    ("{channel}", "Channel name"),
    ("{resolution}", "Selected resolution (e.g. 1080p)"),
    ("{date}", "Download date (YYYYMMDD)"),
    ("{year}", "Year (YYYY)"),
    ("{month}", "Month (MM)"),
    ("{day}", "Day (DD)"),
    ("{ext}", "File extension (e.g. mp4)"),
    ("{id}", "Short task ID (8 chars)"),
]

# Set of known variable names (without braces) for validation
_KNOWN_VARS: frozenset[str] = frozenset(var[1:-1] for var, _ in AVAILABLE_VARIABLES)


def render_template(
    template: str,
    title: str,
    channel: str,
    resolution: str,
    ext: str,
    task_id: str = "",
) -> str:
    """Render *template* with the provided values and sanitize the result.

    Returns a filename without extension (extension is handled separately by
    yt-dlp).  Falls back to the sanitized title if the template raises a
    formatting error.

    Args:
        template:   Format string using ``{variable}`` placeholders.
        title:      Raw video title.
        channel:    Channel or uploader name (may be empty).
        resolution: Resolution string such as ``"1080p"`` or ``"Best"``.
        ext:        File extension with or without a leading dot.
        task_id:    UUID string; only the first 8 characters are used.

    Returns:
        A sanitized filename stem (no extension, no leading/trailing spaces).
    """
    from datetime import date as _date

    today = _date.today()
    sanitized_title = sanitize_filename(title)
    mapping: dict[str, str] = {
        "title": sanitized_title,
        "channel": sanitize_filename(channel) if channel else "Unknown",
        "resolution": resolution or "best",
        "date": today.strftime("%Y%m%d"),
        "year": today.strftime("%Y"),
        "month": today.strftime("%m"),
        "day": today.strftime("%d"),
        "ext": ext.lstrip(".").lower() if ext else "",
        "id": task_id[:8] if task_id else "",
    }
    try:
        result = template.format_map(mapping)
    except (KeyError, ValueError):
        # Fallback: plain sanitized title on any bad template
        result = sanitized_title
    return sanitize_filename(result) or sanitized_title


def validate_template(template: str) -> tuple[bool, str]:
    """Check *template* for unknown variables.

    Args:
        template: Format string to validate.

    Returns:
        A ``(is_valid, error_message)`` tuple.  ``error_message`` is an empty
        string when the template is valid.
    """
    formatter = string.Formatter()
    try:
        field_names: list[str] = [
            fname
            for _, fname, _, _ in formatter.parse(template)
            if fname is not None
        ]
    except ValueError as exc:
        return False, str(exc)

    unknown: list[str] = [f for f in field_names if f and f not in _KNOWN_VARS]
    if unknown:
        return False, (
            "Unknown variable(s): "
            + ", ".join("{" + u + "}" for u in unknown)
        )
    return True, ""
