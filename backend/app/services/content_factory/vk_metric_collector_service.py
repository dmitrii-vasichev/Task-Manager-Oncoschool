from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

VK_WALL_GET_BY_ID_URL = "https://api.vk.com/method/wall.getById"
VK_WALL_GET_COMMENTS_URL = "https://api.vk.com/method/wall.getComments"
VK_METRIC_WINDOWS = ("3h", "24h", "72h", "7d", "final")
VK_WALL_REF_PATTERN = re.compile(r"(?:wall)?(-?\d+)_(\d+)")


class VKMetricCollectorError(ValueError):
    """Raised when VK metric collection cannot proceed safely."""


@dataclass(frozen=True)
class VKPostIdentity:
    owner_id: int
    post_id: int

    @property
    def as_vk_ref(self) -> str:
        return f"{self.owner_id}_{self.post_id}"


@dataclass(frozen=True)
class VKPostMetrics:
    owner_id: int
    post_id: int
    counters: dict[str, int]
    raw_post: dict[str, Any]
    raw_comments: dict[str, Any]


def _coerce_int(value: Any, label: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        raise VKMetricCollectorError(f"Invalid VK {label}") from None


def parse_vk_post_identity(
    platform_post_id: str | None,
    platform_post_url: str | None,
    *,
    fallback_owner_id: int | None,
) -> VKPostIdentity:
    for candidate in (platform_post_id, platform_post_url):
        if not candidate:
            continue
        match = VK_WALL_REF_PATTERN.search(str(candidate))
        if match:
            return VKPostIdentity(
                owner_id=_coerce_int(match.group(1), "owner id"),
                post_id=_coerce_int(match.group(2), "post id"),
            )

    if platform_post_id and str(platform_post_id).strip().isdigit():
        if fallback_owner_id is None:
            raise VKMetricCollectorError("VK owner id is required for plain post ids")
        return VKPostIdentity(
            owner_id=fallback_owner_id,
            post_id=_coerce_int(platform_post_id, "post id"),
        )

    raise VKMetricCollectorError("VK post identity is missing or invalid")


def due_metric_windows(
    *,
    published_at: datetime,
    now: datetime,
    configured_windows: list[str] | tuple[str, ...],
    final_after_days: int,
) -> list[str]:
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age = now - published_at
    thresholds = {
        "3h": timedelta(hours=3),
        "24h": timedelta(hours=24),
        "72h": timedelta(hours=72),
        "7d": timedelta(days=7),
        "final": timedelta(days=final_after_days),
    }
    return [
        window
        for window in configured_windows
        if window in thresholds and age >= thresholds[window]
    ]


class VKMetricsClient:
    def __init__(
        self,
        *,
        access_token: str,
        api_version: str,
        async_client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self.access_token = access_token
        self.api_version = api_version
        self.async_client_factory = async_client_factory or httpx.AsyncClient

    async def fetch_post_metrics(self, *, owner_id: int, post_id: int) -> VKPostMetrics:
        post_data = await self._post(
            VK_WALL_GET_BY_ID_URL,
            {
                "posts": f"{owner_id}_{post_id}",
                "access_token": self.access_token,
                "v": self.api_version,
            },
        )
        post_items = post_data.get("response", {}).get("items", [])
        if not post_items:
            raise VKMetricCollectorError("VK post was not found")
        post = post_items[0]

        comments_data = await self._post(
            VK_WALL_GET_COMMENTS_URL,
            {
                "owner_id": owner_id,
                "post_id": post_id,
                "count": 0,
                "access_token": self.access_token,
                "v": self.api_version,
            },
        )

        counters: dict[str, int] = {}
        for metric_name, path in {
            "views": ("views", "count"),
            "likes": ("likes", "count"),
            "reposts": ("reposts", "count"),
        }.items():
            value = post.get(path[0], {}).get(path[1])
            if isinstance(value, int):
                counters[metric_name] = value

        comments_count = comments_data.get("response", {}).get("count")
        if isinstance(comments_count, int):
            counters["comments"] = comments_count

        return VKPostMetrics(
            owner_id=owner_id,
            post_id=post_id,
            counters=counters,
            raw_post=post,
            raw_comments=comments_data.get("response", {}),
        )

    async def _post(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self.async_client_factory() as client:
                response = await client.post(url, data=data, timeout=15)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise VKMetricCollectorError(
                f"VK metrics request failed: {str(exc)[:500]}"
            ) from exc

        if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
            error = payload["error"]
            code = error.get("error_code")
            message = error.get("error_msg") or "unknown VK error"
            raise VKMetricCollectorError(
                f"VK API rejected metrics request: {code} {message}"
            )
        if not isinstance(payload, dict):
            raise VKMetricCollectorError("VK metrics request returned invalid JSON")
        return payload
