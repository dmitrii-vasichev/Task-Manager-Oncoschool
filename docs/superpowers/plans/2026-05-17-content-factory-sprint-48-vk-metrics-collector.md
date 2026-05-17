# Content Factory Sprint 48 VK Metrics Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real automated Content Factory metric source by importing VK post counters into `cf_metric_snapshot`.

**Architecture:** Add a focused backend VK metric collector service with three testable boundaries: post identity parsing, VK HTTP client mapping, and collector orchestration. The collector writes snapshots through the existing Sprint 47 `MetricService.record_deduped`, records import run audit data through `MetricImportRunService`, exposes a manual run endpoint, and runs automatically only when active `vk_api` metric sources exist.

**Tech Stack:** FastAPI, SQLAlchemy async ORM, APScheduler, httpx, Pydantic, Node test runner for frontend source guards, TypeScript API client.

---

## File Structure

- Create `backend/app/services/content_factory/vk_metric_collector_service.py`: VK post identity parser, VK metrics client, due-window helpers, collector orchestration, and collector-specific errors.
- Create `backend/app/services/content_factory/metric_import_scheduler_service.py`: APScheduler wrapper that loads active `vk_api` sources and invokes the collector.
- Modify `backend/app/db/schemas.py`: add `CFMetricSourceRunRequest`.
- Modify `backend/app/api/content_factory/metric_sources.py`: add `POST /metric-sources/{source_config_id}/run`.
- Modify `backend/app/config.py`: add metric import scheduler settings.
- Modify `backend/app/main.py`: instantiate/start/stop metric import scheduler.
- Create `backend/tests/test_cf_vk_metric_collector_service.py`: parser, client, due-window, collector, dedupe, and error behavior.
- Create `backend/tests/test_cf_metric_import_scheduler_service.py`: scheduler source loading and error containment.
- Modify `backend/tests/test_content_factory_metric_sources_api.py`: manual run endpoint tests.
- Modify `frontend/src/lib/types.ts`: add `CFMetricSourceRunRequest`.
- Modify `frontend/src/lib/api.ts`: add `runCFMetricSource`.
- Modify `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`: source guard for new API method.
- Modify durable docs: `docs/PLAN.md`, `docs/STATUS.md`, `docs/TEST_PLAN.md`, `docs/BACKLOG.md`.

---

### Task 1: VK Metric Collector Parser And Client

**Files:**
- Create: `backend/tests/test_cf_vk_metric_collector_service.py`
- Create: `backend/app/services/content_factory/vk_metric_collector_service.py`

- [ ] **Step 1: Write failing parser, due-window, and client tests**

Add these tests to `backend/tests/test_cf_vk_metric_collector_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_vk_metric_collector_service.py -q
```

Expected: fail with `ModuleNotFoundError: No module named 'app.services.content_factory.vk_metric_collector_service'`.

- [ ] **Step 3: Implement parser, due-window helper, and VK client**

Create `backend/app/services/content_factory/vk_metric_collector_service.py` with:

```python
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
```

- [ ] **Step 4: Run tests to verify GREEN**

Run the same pytest command. Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/content_factory/vk_metric_collector_service.py backend/tests/test_cf_vk_metric_collector_service.py
git commit -m "feat(cf): add vk metric collector client"
```

---

### Task 2: Collector Orchestration

**Files:**
- Modify: `backend/app/services/content_factory/vk_metric_collector_service.py`
- Modify: `backend/tests/test_cf_vk_metric_collector_service.py`

- [ ] **Step 1: Write failing collector tests**

Append tests that instantiate `VKMetricCollectorService` with fake dependencies:

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app.services.content_factory.vk_metric_collector_service import (
    VKMetricCollectorService,
    VKPostMetrics,
)


@pytest.mark.asyncio
async def test_vk_metric_collector_records_due_snapshots_with_provenance():
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = [
        SimpleNamespace(
            id=uuid.uuid4(),
            published_at=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
            platform_post_id="-123_456",
            platform_post_url=None,
        )
    ]
    session.add = Mock()
    run = SimpleNamespace(id=uuid.uuid4(), status="running", source_config=None)
    source_config = SimpleNamespace(
        id=uuid.uuid4(),
        source="vk_api",
        config={"owner_id": "-123", "windows": ["24h"]},
        default_confidence="high",
        freshness_window_hours=24,
    )

    import_run_service = SimpleNamespace(
        start_run=AsyncMock(return_value=run),
        finish_run=AsyncMock(side_effect=lambda session, run, **kwargs: SimpleNamespace(**kwargs, id=run.id)),
    )
    metric_service = SimpleNamespace(
        record_deduped=AsyncMock(
            side_effect=[
                SimpleNamespace(snapshot=SimpleNamespace(id=uuid.uuid4()), created=True),
                SimpleNamespace(snapshot=SimpleNamespace(id=uuid.uuid4()), created=True),
            ]
        )
    )
    client = SimpleNamespace(
        fetch_post_metrics=AsyncMock(
            return_value=VKPostMetrics(
                owner_id=-123,
                post_id=456,
                counters={"views": 1000, "likes": 40},
                raw_post={"id": 456},
                raw_comments={"count": 9},
            )
        )
    )
    collector = VKMetricCollectorService(
        client_factory=lambda access_token, api_version: client,
        import_run_service=import_run_service,
        metric_service=metric_service,
        access_token="token",
        default_owner_id=None,
        default_api_version="5.199",
        now_provider=lambda: datetime(2026, 5, 11, 13, 0, tzinfo=timezone.utc),
    )

    result = await collector.collect_for_source(
        session,
        source_config,
        triggered_by="manual",
    )

    assert result.status == "succeeded"
    assert result.found_count == 2
    assert result.created_count == 2
    first_payload = metric_service.record_deduped.await_args_list[0].args[1]
    assert first_payload.publication_id == session.execute.return_value.scalars.return_value.all.return_value[0].id
    assert first_payload.window == "24h"
    assert first_payload.metric_name == "views"
    assert first_payload.source == "vk_api"
    assert first_payload.source_method == "vk_api.wall.getById"
    assert first_payload.confidence == "high"
    assert first_payload.source_config_id == source_config.id
    assert first_payload.import_run_id == run.id
    assert first_payload.external_metric_id == "-123_456:views"
    assert first_payload.dedupe_key.endswith(":24h:views")


@pytest.mark.asyncio
async def test_vk_metric_collector_skips_duplicate_snapshots():
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = [
        SimpleNamespace(
            id=uuid.uuid4(),
            published_at=datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc),
            platform_post_id="-123_456",
            platform_post_url=None,
        )
    ]
    source_config = SimpleNamespace(
        id=uuid.uuid4(),
        source="vk_api",
        config={"owner_id": "-123", "windows": ["24h"]},
        default_confidence="medium",
        freshness_window_hours=24,
    )
    run = SimpleNamespace(id=uuid.uuid4(), status="running", source_config=None)
    import_run_service = SimpleNamespace(
        start_run=AsyncMock(return_value=run),
        finish_run=AsyncMock(side_effect=lambda session, run, **kwargs: SimpleNamespace(**kwargs, id=run.id)),
    )
    metric_service = SimpleNamespace(
        record_deduped=AsyncMock(
            return_value=SimpleNamespace(snapshot=SimpleNamespace(id=uuid.uuid4()), created=False)
        )
    )
    client = SimpleNamespace(
        fetch_post_metrics=AsyncMock(
            return_value=VKPostMetrics(
                owner_id=-123,
                post_id=456,
                counters={"views": 1000},
                raw_post={"id": 456},
                raw_comments={"count": 0},
            )
        )
    )
    collector = VKMetricCollectorService(
        client_factory=lambda access_token, api_version: client,
        import_run_service=import_run_service,
        metric_service=metric_service,
        access_token="token",
        default_owner_id=None,
        default_api_version="5.199",
        now_provider=lambda: datetime(2026, 5, 11, 13, 0, tzinfo=timezone.utc),
    )

    result = await collector.collect_for_source(session, source_config, triggered_by="manual")

    assert result.created_count == 0
    assert result.skipped_duplicate_count == 1


@pytest.mark.asyncio
async def test_vk_metric_collector_marks_partial_when_publication_fails():
    session = AsyncMock()
    session.execute.return_value.scalars.return_value.all.return_value = [
        SimpleNamespace(id=uuid.uuid4(), published_at=datetime.now(timezone.utc), platform_post_id="bad", platform_post_url=None)
    ]
    source_config = SimpleNamespace(
        id=uuid.uuid4(),
        source="vk_api",
        config={"owner_id": "-123", "windows": ["3h"]},
        default_confidence="medium",
        freshness_window_hours=24,
    )
    run = SimpleNamespace(id=uuid.uuid4(), status="running", source_config=None)
    import_run_service = SimpleNamespace(
        start_run=AsyncMock(return_value=run),
        finish_run=AsyncMock(side_effect=lambda session, run, **kwargs: SimpleNamespace(**kwargs, id=run.id)),
    )
    collector = VKMetricCollectorService(
        import_run_service=import_run_service,
        access_token="token",
        default_owner_id=None,
        default_api_version="5.199",
        now_provider=lambda: datetime.now(timezone.utc) + timedelta(hours=4),
    )

    result = await collector.collect_for_source(session, source_config, triggered_by="manual")

    assert result.status == "failed"
    assert result.error_count == 1
    assert "failed" in result.error_message.lower()


@pytest.mark.asyncio
async def test_vk_metric_collector_rejects_missing_token_before_external_calls():
    session = AsyncMock()
    source_config = SimpleNamespace(
        id=uuid.uuid4(),
        source="vk_api",
        config={"owner_id": "-123"},
        default_confidence="medium",
        freshness_window_hours=24,
    )
    collector = VKMetricCollectorService(access_token="", default_owner_id=None)

    with pytest.raises(VKMetricCollectorError, match="token"):
        await collector.collect_for_source(session, source_config, triggered_by="manual")
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_vk_metric_collector_service.py -q
```

Expected: fail because `VKMetricCollectorService` does not exist.

- [ ] **Step 3: Implement collector orchestration**

Add the collector, config helpers, publication query, and snapshot recording to `vk_metric_collector_service.py`. The implementation should use:

```python
from app.config import settings
from app.db.models import CFMetricSourceConfig, CFPlatform, CFPublication
from app.db.schemas import CFMetricSnapshotCreate
from app.services.content_factory.metric_service import MetricService
from app.services.content_factory.metric_source_service import MetricImportRunService
```

Core signatures:

```python
class VKMetricCollectorService:
    def __init__(
        self,
        *,
        client_factory: Callable[[str, str], Any] | None = None,
        import_run_service=MetricImportRunService,
        metric_service=MetricService,
        access_token: str | None = None,
        default_owner_id: int | None = None,
        default_api_version: str | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None: ...

    async def collect_for_source(
        self,
        session: AsyncSession,
        source_config: CFMetricSourceConfig,
        *,
        triggered_by: str = "manual",
        requested_by_id: uuid.UUID | None = None,
        publication_id: uuid.UUID | None = None,
    ): ...
```

Use `select(CFPublication).join(CFPlatform)` with filters for `CFPlatform.code == "vk"`, `CFPublication.status == "published"`, and optional publication id. Build `CFMetricSnapshotCreate` for each counter/window.

- [ ] **Step 4: Run tests to verify GREEN**

Run the same pytest command. Expected: all collector tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/content_factory/vk_metric_collector_service.py backend/tests/test_cf_vk_metric_collector_service.py
git commit -m "feat(cf): collect vk post metrics"
```

---

### Task 3: Manual Run API

**Files:**
- Modify: `backend/app/db/schemas.py`
- Modify: `backend/app/api/content_factory/metric_sources.py`
- Modify: `backend/tests/test_content_factory_metric_sources_api.py`

- [ ] **Step 1: Write failing API tests**

Add tests for `run_metric_source` in `backend/tests/test_content_factory_metric_sources_api.py` using the existing direct-call style:

```python
@pytest.mark.asyncio
async def test_run_metric_source_invokes_vk_collector(monkeypatch):
    source_id = uuid.uuid4()
    member = SimpleNamespace(id=uuid.uuid4())
    source = SimpleNamespace(id=source_id, source="vk_api")
    run = SimpleNamespace(
        id=uuid.uuid4(),
        source_config_id=source_id,
        status="succeeded",
        triggered_by="manual",
        requested_by_id=member.id,
        started_at=None,
        finished_at=None,
        found_count=4,
        created_count=4,
        skipped_duplicate_count=0,
        error_count=0,
        error_message=None,
        raw_summary={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session = AsyncMock()

    monkeypatch.setattr(metric_sources.source_config_service, "get", AsyncMock(return_value=source))
    collector = SimpleNamespace(collect_for_source=AsyncMock(return_value=run))
    monkeypatch.setattr(metric_sources, "vk_metric_collector", collector)

    result = await metric_sources.run_metric_source(
        source_id,
        CFMetricSourceRunRequest(publication_id=None, force=False),
        member=member,
        session=session,
    )

    assert result is run
    collector.collect_for_source.assert_awaited_once_with(
        session,
        source,
        triggered_by="manual",
        requested_by_id=member.id,
        publication_id=None,
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_metric_source_rejects_force():
    with pytest.raises(HTTPException) as exc_info:
        await metric_sources.run_metric_source(
            uuid.uuid4(),
            CFMetricSourceRunRequest(force=True),
            member=SimpleNamespace(id=uuid.uuid4()),
            session=AsyncMock(),
        )

    assert exc_info.value.status_code == 400
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_metric_sources_api.py -q
```

Expected: fail because `CFMetricSourceRunRequest` or `run_metric_source` does not exist.

- [ ] **Step 3: Implement schema and endpoint**

Add to `backend/app/db/schemas.py`:

```python
class CFMetricSourceRunRequest(BaseModel):
    publication_id: uuid.UUID | None = None
    force: bool = False
```

Modify `metric_sources.py`:

```python
from app.services.content_factory.vk_metric_collector_service import (
    VKMetricCollectorError,
    VKMetricCollectorService,
)

vk_metric_collector = VKMetricCollectorService()

@router.post(
    "/metric-sources/{source_config_id}/run",
    response_model=CFMetricImportRunResponse,
)
async def run_metric_source(...):
    if data.force:
        raise HTTPException(status_code=400, detail="force mode is not supported yet")
    source = await source_config_service.get(session, source_config_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Источник метрик не найден")
    if source.source != "vk_api":
        raise HTTPException(status_code=400, detail="Автосбор метрик пока поддерживает только VK API")
    try:
        run = await vk_metric_collector.collect_for_source(...)
    except VKMetricCollectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await session.commit()
    return run
```

- [ ] **Step 4: Run tests to verify GREEN**

Run the same pytest command. Expected: metric source API tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/schemas.py backend/app/api/content_factory/metric_sources.py backend/tests/test_content_factory_metric_sources_api.py
git commit -m "feat(cf): expose vk metric import run"
```

---

### Task 4: Metric Import Scheduler

**Files:**
- Create: `backend/app/services/content_factory/metric_import_scheduler_service.py`
- Create: `backend/tests/test_cf_metric_import_scheduler_service.py`
- Modify: `backend/app/config.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing scheduler tests**

Create `backend/tests/test_cf_metric_import_scheduler_service.py`:

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.content_factory.metric_import_scheduler_service import (
    ContentFactoryMetricImportSchedulerService,
)


@pytest.mark.asyncio
async def test_metric_import_scheduler_collects_active_vk_sources():
    source = SimpleNamespace(id="source-1", source="vk_api")
    session = AsyncMock()
    source_config_service = SimpleNamespace(list=AsyncMock(return_value=[source]))
    collector = SimpleNamespace(collect_for_source=AsyncMock())

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scheduler = ContentFactoryMetricImportSchedulerService(
        session_maker=lambda: SessionContext(),
        collector=collector,
        source_config_service=source_config_service,
        enabled=True,
    )

    await scheduler.collect_due_sources_once()

    collector.collect_for_source.assert_awaited_once_with(
        session,
        source,
        triggered_by="scheduled",
    )


@pytest.mark.asyncio
async def test_metric_import_scheduler_does_nothing_when_disabled():
    source_config_service = SimpleNamespace(list=AsyncMock())
    collector = SimpleNamespace(collect_for_source=AsyncMock())
    scheduler = ContentFactoryMetricImportSchedulerService(
        session_maker=lambda: None,
        collector=collector,
        source_config_service=source_config_service,
        enabled=False,
    )

    await scheduler.collect_due_sources_once()

    source_config_service.list.assert_not_called()
    collector.collect_for_source.assert_not_called()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_metric_import_scheduler_service.py -q
```

Expected: fail because scheduler module does not exist.

- [ ] **Step 3: Implement scheduler and settings**

Add settings to `backend/app/config.py`:

```python
CF_METRIC_IMPORT_ENABLED: bool = True
CF_METRIC_IMPORT_INTERVAL_MINUTES: int = 30
```

Create scheduler with `AsyncIOScheduler`, `start`, `stop`, and `collect_due_sources_once`, following the publishing scheduler pattern. Wire it in `backend/app/main.py` with:

```python
content_factory_metric_import_scheduler = ContentFactoryMetricImportSchedulerService(
    session_maker=async_session,
)
app.state.content_factory_metric_import_scheduler = content_factory_metric_import_scheduler
```

Start on startup and stop on shutdown.

- [ ] **Step 4: Run tests to verify GREEN**

Run scheduler tests. Expected: scheduler tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/main.py backend/app/services/content_factory/metric_import_scheduler_service.py backend/tests/test_cf_metric_import_scheduler_service.py
git commit -m "feat(cf): schedule vk metric imports"
```

---

### Task 5: Frontend API Contract

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/content-factory/contentFactorySourceGuards.test.ts`

- [ ] **Step 1: Write failing source guard**

Add an assertion to `contentFactorySourceGuards.test.ts`:

```ts
test("metric source API exposes manual run endpoint", () => {
  const apiSource = readSource("src/lib/api.ts");
  const typeSource = readSource("src/lib/types.ts");

  assert.match(typeSource, /interface CFMetricSourceRunRequest/);
  assert.match(apiSource, /runCFMetricSource/);
  assert.match(apiSource, /metric-sources\\/\\$\\{sourceConfigId\\}\\/run/);
});
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Expected: fail because `runCFMetricSource` does not exist.

- [ ] **Step 3: Implement frontend types/API method**

Add to `types.ts`:

```ts
export interface CFMetricSourceRunRequest {
  publication_id?: string | null;
  force?: boolean;
}
```

Add to imports and API client:

```ts
async runCFMetricSource(
  sourceConfigId: string,
  data: CFMetricSourceRunRequest = {}
): Promise<CFMetricImportRun> {
  return this.request<CFMetricImportRun>(
    `/api/content-factory/metric-sources/${sourceConfigId}/run`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
}
```

- [ ] **Step 4: Run test to verify GREEN**

Run the same frontend guard command. Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/components/content-factory/contentFactorySourceGuards.test.ts
git commit -m "feat(cf): add metric source run client"
```

---

### Task 6: Durable Docs And Verification

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/TEST_PLAN.md`
- Modify: `docs/BACKLOG.md`

- [ ] **Step 1: Run focused backend and frontend verification**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_vk_metric_collector_service.py tests/test_cf_metric_import_scheduler_service.py tests/test_content_factory_metric_sources_api.py tests/test_content_factory_metrics_api.py -q
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npx tsc --noEmit
git diff --check
```

Expected: focused tests pass. Full DB-dependent backend pytest may still require local Postgres/Docker.

- [ ] **Step 2: Update durable docs**

Add Sprint 48 as the top section in `docs/PLAN.md`, `docs/STATUS.md`, and `docs/TEST_PLAN.md`. Move backlog next item from Sprint 48 to Sprint 49 and add manual QA for Sprint 48.

- [ ] **Step 3: Run final verification**

Run:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_cf_vk_metric_collector_service.py tests/test_cf_metric_import_scheduler_service.py tests/test_content_factory_metric_sources_api.py tests/test_content_factory_metrics_api.py -q
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

- [ ] **Step 4: Commit docs**

```bash
git add docs/PLAN.md docs/STATUS.md docs/TEST_PLAN.md docs/BACKLOG.md
git commit -m "docs(cf): update vk metrics collector status"
```

---

## Self-Review

- Spec coverage: VK source config, eligibility, windows, metrics, service, API, scheduler, frontend API, error handling, tests, and durable docs are all mapped to tasks.
- Placeholder scan: no task uses TBD/TODO placeholders; implementation signatures and endpoint paths are explicit.
- Type consistency: service, schema, endpoint, frontend method, and test names use the same `VKMetricCollectorService`, `CFMetricSourceRunRequest`, and `runCFMetricSource` names.
