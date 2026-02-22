import unittest
from datetime import datetime

from app.api.meetings import _build_meeting_deleted_message_html


class MeetingDeleteNotificationTemplateTests(unittest.TestCase):
    def test_meeting_deleted_message_uses_attention_header_and_spacing(self) -> None:
        message = _build_meeting_deleted_message_html(
            title="Встреча по обновлению функционала",
            meeting_date=datetime(2026, 3, 2, 12, 0),
            participants_mentions="@darya_pleshkova @demetrioni",
        )

        self.assertIn(
            "Внимание! ⚠️\n\nВстреча <b>Встреча по обновлению функционала</b> отменена.",
            message,
        )
        self.assertIn("отменена.\n\nДата/время: <b>02.03.2026 15:00 МСК</b>", message)
        self.assertIn(
            "Дата/время: <b>02.03.2026 15:00 МСК</b>\n\nУчастники: @darya_pleshkova @demetrioni",
            message,
        )
        self.assertNotIn("Добрый день!", message)

    def test_meeting_deleted_message_omits_optional_sections_when_empty(self) -> None:
        message = _build_meeting_deleted_message_html(
            title="",
            meeting_date=None,
            participants_mentions="",
        )

        self.assertEqual(
            message,
            "Внимание! ⚠️\n\nВстреча <b>Встреча</b> отменена.",
        )
