import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.content_factory.vk_metric_collector_service import (
    VKMetricCollectorError,
    VKMetricsClient,
    due_metric_windows,
    parse_vk_post_identity,
)


def test_parse_vk_post_identity_supports_ids_and_urls():
    assert parse_vk_post_identity("456", None, fallback_owner_id=-123).as_vk_ref == "-123_456"
    assert parse_vk_post_identity("-123_456", None, fallback_owner_id=None).as_vk_ref == "-123_456"
    assert parse_vk_post_identity("wall-123_456", None, fallback_owner_id=None).as_vk_ref == "-123_456"
    assert (
        parse_vk_post_identity(
            None,
            "https://vk.com/wall-123_456?from=feed",
            fallback_owner_id=None,
        ).as_vk_ref
        == "-123_456"
    )


def test_parse_vk_post_identity_requires_owner_for_plain_post_id():
    with pytest.raises(VKMetricCollectorError, match="owner id"):
        parse_vk_post_identity("456", None, fallback_owner_id=None)


def test_due_metric_windows_uses_age_and_configured_windows():
    published_at = datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
    now = published_at + timedelta(days=3, hours=1)

    assert due_metric_windows(
        published_at=published_at,
        now=now,
        configured_windows=["3h", "24h", "72h", "7d", "final"],
        final_after_days=30,
    ) == ["3h", "24h", "72h"]


@pytest.mark.asyncio
async def test_vk_metrics_client_maps_post_and_comment_counters():
    requests = []

    async def fake_post(url, data, timeout):
        requests.append((url, data, timeout))

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                if data.get("post_id"):
                    return {"response": {"count": 9, "items": []}}
                return {
                    "response": {
                        "items": [
                            {
                                "id": 456,
                                "owner_id": -123,
                                "views": {"count": 1000},
                                "likes": {"count": 40},
                                "reposts": {"count": 7},
                            }
                        ]
                    }
                }

        return Response()

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        post = staticmethod(fake_post)

    client = VKMetricsClient(
        access_token="token",
        api_version="5.199",
        async_client_factory=FakeAsyncClient,
    )

    metrics = await client.fetch_post_metrics(owner_id=-123, post_id=456)

    assert metrics.counters == {
        "views": 1000,
        "likes": 40,
        "reposts": 7,
        "comments": 9,
    }
    assert requests[0][1]["posts"] == "-123_456"
    assert requests[1][1]["owner_id"] == -123
    assert requests[1][1]["post_id"] == 456


@pytest.mark.asyncio
async def test_vk_metrics_client_raises_on_vk_error_without_token_leak():
    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, data, timeout):
            class Response:
                def raise_for_status(self):
                    return None

                def json(self):
                    return {"error": {"error_code": 5, "error_msg": "User authorization failed"}}

            return Response()

    client = VKMetricsClient(
        access_token="super-secret-token",
        api_version="5.199",
        async_client_factory=FakeAsyncClient,
    )

    with pytest.raises(VKMetricCollectorError) as exc_info:
        await client.fetch_post_metrics(owner_id=-123, post_id=456)

    assert "super-secret-token" not in str(exc_info.value)
    assert "VK API rejected metrics request" in str(exc_info.value)
