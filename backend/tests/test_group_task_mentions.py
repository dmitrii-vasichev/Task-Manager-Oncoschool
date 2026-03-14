import uuid
import unittest
from types import SimpleNamespace

from app.bot.handlers.tasks import (
    _extract_username_mentions,
    _message_mentions_bot,
    _resolve_group_task_assignee,
)


def _member(full_name: str, *, username: str | None, telegram_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        full_name=full_name,
        telegram_username=username,
        telegram_id=telegram_id,
        name_variants=[],
    )


class GroupTaskMentionTests(unittest.TestCase):
    def test_extract_username_mentions_normalizes_and_deduplicates(self) -> None:
        mentions = _extract_username_mentions(
            "Сделать отчёт @Demo_Bot и передать @ivan_ivanov, затем снова @demo_bot"
        )
        self.assertEqual(mentions, ["demo_bot", "ivan_ivanov"])

    def test_message_mentions_bot_by_text_mention_entity(self) -> None:
        message = SimpleNamespace(
            text="Поставь задачу, пожалуйста",
            entities=[SimpleNamespace(type="text_mention", user=SimpleNamespace(id=77))],
        )
        self.assertTrue(
            _message_mentions_bot(
                message,
                bot_username="demo_bot",
                bot_user_id=77,
            )
        )

    def test_resolve_group_assignee_prefers_explicit_username(self) -> None:
        creator = _member("Автор задачи", username="author", telegram_id=1)
        ivan = _member("Иван Иванов", username="ivan_ivanov", telegram_id=2)

        assignee_id, assignee_name, assignee_note = _resolve_group_task_assignee(
            creator=creator,
            team_members=[creator, ivan],
            explicit_usernames=["ivan_ivanov"],
            explicit_text_mention_ids=[],
            parsed_assignee_name="Автор задачи",
        )

        self.assertEqual(assignee_id, ivan.id)
        self.assertEqual(assignee_name, "Иван Иванов")
        self.assertIsNone(assignee_note)

    def test_resolve_group_assignee_falls_back_when_name_is_ambiguous(self) -> None:
        creator = _member("Пётр Петров", username="petr", telegram_id=1)
        ivan_one = _member("Иван Иванов", username="ivan_one", telegram_id=2)
        ivan_two = _member("Иван Петров", username="ivan_two", telegram_id=3)

        assignee_id, assignee_name, assignee_note = _resolve_group_task_assignee(
            creator=creator,
            team_members=[creator, ivan_one, ivan_two],
            explicit_usernames=[],
            explicit_text_mention_ids=[],
            parsed_assignee_name="Иван",
        )

        self.assertEqual(assignee_id, creator.id)
        self.assertEqual(assignee_name, creator.full_name)
        self.assertIsNotNone(assignee_note)
        self.assertIn("неоднозначно", assignee_note)


if __name__ == "__main__":
    unittest.main()
