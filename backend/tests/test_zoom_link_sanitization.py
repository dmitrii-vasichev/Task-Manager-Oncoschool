import unittest

from app.services.zoom_service import extract_zoom_join_url, sanitize_zoom_join_url


class ZoomLinkSanitizationTests(unittest.TestCase):
    def test_sanitize_start_url_to_join_url(self) -> None:
        raw_url = "https://us06web.zoom.us/s/12345678901?zak=secret-token&pwd=meeting-pass"

        safe_url = sanitize_zoom_join_url(raw_url)

        self.assertEqual(
            safe_url,
            "https://us06web.zoom.us/j/12345678901?pwd=meeting-pass",
        )

    def test_sanitize_removes_host_token_from_join_url(self) -> None:
        raw_url = "https://zoom.us/j/12345678901?pwd=meeting-pass&zak=secret-token"

        safe_url = sanitize_zoom_join_url(raw_url)

        self.assertEqual(safe_url, "https://zoom.us/j/12345678901?pwd=meeting-pass")

    def test_extract_fallback_to_start_url(self) -> None:
        zoom_data = {
            "id": "9988776655",
            "start_url": "https://zoom.us/s/9988776655?zak=secret-token&pwd=abc123",
        }

        safe_url = extract_zoom_join_url(zoom_data)

        self.assertEqual(safe_url, "https://zoom.us/j/9988776655?pwd=abc123")

