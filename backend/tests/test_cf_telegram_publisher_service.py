import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.content_factory.telegram_publisher_service import (
    CONTENT_FACTORY_TARGET_TYPE,
    TelegramPublisherError,
    TelegramPublisherService,
    build_telegram_message,
)


def make_publication(**overrides):
    base = {
        "id": uuid.uuid4(),
        "platform_id": uuid.uuid4(),
        "title": "Original <Title>",
        "body_text": "Original body & CTA",
        "media_refs": [],
        "status": "scheduled",
        "version_number": 4,
        "utm": {},
        "actual_published_at": None,
        "platform_post_id": None,
        "platform_post_url": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_variant(**overrides):
    base = {
        "channel": "telegram",
        "title": "Variant <Title>",
        "body_text": "Variant body & CTA",
        "source_version_number": 4,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_target(**overrides):
    base = {
        "id": uuid.uuid4(),
        "chat_id": -1001234567890,
        "thread_id": None,
        "label": "Content Factory",
        "types": [CONTENT_FACTORY_TARGET_TYPE],
        "is_active": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_queue_item(publication=None, **overrides):
    publication = publication or make_publication()
    base = {
        "id": uuid.uuid4(),
        "publication_id": publication.id,
        "platform_id": publication.platform_id,
        "payload": {"utm": publication.utm},
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def make_platform(**overrides):
    base = {"id": uuid.uuid4(), "code": "telegram", "display_name": "Telegram"}
    base.update(overrides)
    return SimpleNamespace(**base)


def make_service(target_repo=None):
    return TelegramPublisherService(
        target_repo=target_repo or SimpleNamespace(
            get_by_id=AsyncMock(),
            get_active_by_type=AsyncMock(),
        )
    )


def test_builds_escaped_message_from_current_telegram_variant():
    publication = make_publication()
    variant = make_variant()

    message = build_telegram_message(publication, variant)

    assert message == "<b>Variant &lt;Title&gt;</b>\n\nVariant body &amp; CTA"


@pytest.mark.asyncio
async def test_resolves_explicit_utm_target_id():
    target = make_target()
    target_repo = SimpleNamespace(
        get_by_id=AsyncMock(return_value=target),
        get_active_by_type=AsyncMock(return_value=[]),
    )
    service = make_service(target_repo)
    publication = make_publication(utm={"telegram_target_id": str(target.id)})
    item = make_queue_item(publication)

    result = await service.resolve_target(AsyncMock(), publication, item)

    assert result is target
    target_repo.get_by_id.assert_awaited_once()
    target_repo.get_active_by_type.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolves_single_content_factory_target():
    target = make_target()
    target_repo = SimpleNamespace(
        get_by_id=AsyncMock(),
        get_active_by_type=AsyncMock(return_value=[target]),
    )
    service = make_service(target_repo)
    session = AsyncMock()

    result = await service.resolve_target(
        session,
        make_publication(),
        make_queue_item(),
    )

    assert result is target
    target_repo.get_active_by_type.assert_awaited_once_with(
        session,
        CONTENT_FACTORY_TARGET_TYPE,
    )


@pytest.mark.asyncio
async def test_rejects_missing_or_ambiguous_target():
    target_repo = SimpleNamespace(
        get_by_id=AsyncMock(),
        get_active_by_type=AsyncMock(return_value=[]),
    )
    service = make_service(target_repo)

    with pytest.raises(TelegramPublisherError) as exc:
        await service.resolve_target(AsyncMock(), make_publication(), make_queue_item())

    assert "настройте одну активную группу" in str(exc.value)

    target_repo.get_active_by_type.return_value = [make_target(), make_target()]
    with pytest.raises(TelegramPublisherError) as ambiguous_exc:
        await service.resolve_target(AsyncMock(), make_publication(), make_queue_item())

    assert "Найдено несколько Telegram-групп" in str(ambiguous_exc.value)


@pytest.mark.asyncio
async def test_rejects_media_refs_before_sending(monkeypatch):
    service = make_service()
    publication = make_publication(media_refs=["image.png"])
    item = make_queue_item(publication)
    bot = SimpleNamespace(send_message=AsyncMock())
    monkeypatch.setattr(service, "load_publication", AsyncMock(return_value=publication))
    monkeypatch.setattr(service, "load_platform", AsyncMock(return_value=make_platform()))

    with pytest.raises(TelegramPublisherError) as exc:
        await service.publish(AsyncMock(), item, bot=bot)

    assert "только текстовые публикации" in str(exc.value)
    bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_message_returns_provider_evidence(monkeypatch):
    target = make_target(thread_id=42)
    service = make_service()
    publication = make_publication()
    item = make_queue_item(publication)
    bot = SimpleNamespace(
        send_message=AsyncMock(
            return_value=SimpleNamespace(
                message_id=321,
                date=datetime(2026, 5, 20, 12, 0, tzinfo=UTC),
            )
        )
    )
    monkeypatch.setattr(service, "load_publication", AsyncMock(return_value=publication))
    monkeypatch.setattr(service, "load_platform", AsyncMock(return_value=make_platform()))
    monkeypatch.setattr(service, "load_current_variant", AsyncMock(return_value=None))
    monkeypatch.setattr(service, "resolve_target", AsyncMock(return_value=target))

    result = await service.publish(AsyncMock(), item, bot=bot)

    assert result["platform"] == "telegram"
    assert result["message_id"] == "321"
    assert result["chat_id"] == target.chat_id
    assert result["thread_id"] == target.thread_id
    assert result["post_url"] == "https://t.me/c/1234567890/321"
    bot.send_message.assert_awaited_once_with(
        chat_id=target.chat_id,
        text="<b>Original &lt;Title&gt;</b>\n\nOriginal body &amp; CTA",
        parse_mode="HTML",
        message_thread_id=target.thread_id,
    )
