"""
Unit tests for app.utils.validators.
"""

from __future__ import annotations

import unittest

from app.utils.validators import is_valid_youtube_url, sanitize_filename


class TestIsValidYoutubeUrl(unittest.TestCase):
    """Tests for is_valid_youtube_url."""

    # --- valid URLs ---

    def test_standard_watch_url(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertTrue(is_valid_youtube_url(url))

    def test_watch_url_without_www(self) -> None:
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertTrue(is_valid_youtube_url(url))

    def test_watch_url_without_scheme(self) -> None:
        url = "youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertTrue(is_valid_youtube_url(url))

    def test_short_youtu_be_url(self) -> None:
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertTrue(is_valid_youtube_url(url))

    def test_short_url_without_scheme(self) -> None:
        url = "youtu.be/dQw4w9WgXcQ"
        self.assertTrue(is_valid_youtube_url(url))

    def test_watch_url_with_extra_params(self) -> None:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s&list=PL1234"
        self.assertTrue(is_valid_youtube_url(url))

    def test_http_scheme(self) -> None:
        url = "http://www.youtube.com/watch?v=abc123XYZ-_"
        self.assertTrue(is_valid_youtube_url(url))

    # --- invalid URLs ---

    def test_empty_string(self) -> None:
        self.assertFalse(is_valid_youtube_url(""))

    def test_random_string(self) -> None:
        self.assertFalse(is_valid_youtube_url("not a url at all"))

    def test_other_domain(self) -> None:
        self.assertFalse(is_valid_youtube_url("https://vimeo.com/123456789"))

    def test_youtube_missing_v_param(self) -> None:
        # /watch with no v= parameter should not match
        self.assertFalse(is_valid_youtube_url("https://www.youtube.com/watch?list=PL1234"))

    def test_youtube_channel_url(self) -> None:
        # A channel URL is not a watch URL
        self.assertFalse(is_valid_youtube_url("https://www.youtube.com/c/SomeChannel"))

    def test_whitespace_only(self) -> None:
        self.assertFalse(is_valid_youtube_url("   "))

    def test_youtube_home(self) -> None:
        self.assertFalse(is_valid_youtube_url("https://www.youtube.com/"))


class TestSanitizeFilename(unittest.TestCase):
    """Tests for sanitize_filename."""

    def test_normal_name_passes_through(self) -> None:
        name = "My Video Title 2024"
        self.assertEqual(sanitize_filename(name), name)

    def test_removes_angle_brackets(self) -> None:
        result = sanitize_filename("Video <1> and >2<")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)

    def test_removes_colon(self) -> None:
        result = sanitize_filename("Title: Subtitle")
        self.assertNotIn(":", result)

    def test_removes_slash_and_backslash(self) -> None:
        result = sanitize_filename("path/to\\file")
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)

    def test_removes_pipe_question_asterisk(self) -> None:
        result = sanitize_filename("file|name?with*special")
        self.assertNotIn("|", result)
        self.assertNotIn("?", result)
        self.assertNotIn("*", result)

    def test_removes_double_quotes(self) -> None:
        result = sanitize_filename('Say "hello"')
        self.assertNotIn('"', result)

    def test_truncates_to_200_chars(self) -> None:
        long_name = "A" * 300
        result = sanitize_filename(long_name)
        self.assertEqual(len(result), 200)

    def test_name_exactly_200_chars_unchanged(self) -> None:
        name = "B" * 200
        self.assertEqual(sanitize_filename(name), name)

    def test_name_with_only_illegal_chars_becomes_empty_or_stripped(self) -> None:
        # All illegal chars should be stripped; result may be empty after strip
        result = sanitize_filename('<>:"/\\|?*')
        # Result must contain none of the illegal characters
        for ch in '<>:"/\\|?*':
            self.assertNotIn(ch, result)

    def test_numbers_and_hyphens_preserved(self) -> None:
        name = "Video-2024_HD (1080p)"
        result = sanitize_filename(name)
        self.assertEqual(result, name)

    def test_control_characters_removed(self) -> None:
        # Null byte and other control chars should be stripped
        result = sanitize_filename("title\x00with\x1fnull")
        self.assertNotIn("\x00", result)
        self.assertNotIn("\x1f", result)


if __name__ == "__main__":
    unittest.main()
