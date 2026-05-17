# Content Factory Sprint 48 VK Metrics Collector Design

## Context

Sprint 47 added the metric integration foundation: metric source configs, import runs, snapshot provenance, and dedupe support. Sprint 48 should use that foundation for the first real automated metric source instead of adding another abstract layer.

The most practical first source is VK post metrics. The project already has VK publishing support and stores `platform_post_id` / `platform_post_url` on published Content Factory publications. VK API schema confirms that `wall.getById` returns wall post objects with counters such as likes, reposts, and views, while `wall.getComments` returns a total comment count. Telegram post-level statistics are less suitable for this sprint: Telegram Bot API does not expose normal post analytics, and Telegram Core `stats.getMessageStats` is user/admin MTProto functionality rather than Bot API functionality.

References checked on 2026-05-17:

- VK API schema: `https://github.com/VKCOM/vk-api-schema`
- VK API schema `wall.getById`: `https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/wall/methods.json`
- VK API schema wall objects: `https://raw.githubusercontent.com/VKCOM/vk-api-schema/master/wall/objects.json`
- Telegram Bot API: `https://core.telegram.org/bots/api`
- Telegram message stats: `https://core.telegram.org/method/stats.getMessageStats`
- Telegram channel statistics: `https://core.telegram.org/api/stats`

## Goal

Add a real VK metrics collector that imports post-level metrics for published VK Content Factory publications into `cf_metric_snapshot`, records import run audit data, and can run both manually through the Content Factory API and automatically through a scheduler.

## Non-Goals

- Do not add Telegram metric collection in Sprint 48.
- Do not add email, GetCourse, Dzen, Max, or paid advertising metrics.
- Do not build a full metric source administration UI.
- Do not store VK access tokens in database JSON.
- Do not mutate publication status or publishing queue state from metric collection.
- Do not backfill historical publications without a configured source and an explicit run.

## Source Configuration

Sprint 48 uses the Sprint 47 `cf_metric_source_config` table. A VK collector source must have:

- `source = "vk_api"`.
- `is_active = true` for scheduled collection.
- `config.owner_id`: optional VK wall owner id. If missing, the collector falls back to `settings.VK_OWNER_ID`.
- `config.api_version`: optional VK API version. If missing, the collector falls back to `settings.VK_API_VERSION`.
- `config.windows`: optional list of windows to collect. Default: `["3h", "24h", "72h", "7d"]`.
- `config.final_after_days`: optional integer. Default: `30`. When a publication is at least this old, the collector may write the `final` window.
- `config.publication_limit`: optional integer. Default: `100`.
- `config.batch_size`: optional integer. Default: `50`.
- `credentials_ref`: optional reference such as `env:VK_API_ACCESS_TOKEN`.

The actual VK token comes from `settings.VK_API_ACCESS_TOKEN` in Sprint 48. `config` remains non-secret and continues to reject secret-looking keys.

## Publication Eligibility

The collector considers publications eligible when all of these are true:

- the publication platform code is `vk`;
- the publication status is `published`;
- either `platform_post_id` or `platform_post_url` can identify the VK wall post;
- the publication has a usable `published_at` timestamp for measurement-window selection;
- the relevant metric/window snapshots are not already present by dedupe key.

Post identity parsing should support:

- plain post id from `platform_post_id`, using the configured owner id;
- `owner_id_post_id`, for example `-123_456`;
- `wallowner_post` format, for example `wall-123_456`;
- VK wall URLs containing `wall-123_456`.

If a publication cannot be parsed, it is skipped and counted in the import run summary.

## Measurement Windows

The collector writes one snapshot per metric per due window. A window becomes due when the publication age is at least:

- `3h`: 3 hours after `published_at`;
- `24h`: 24 hours after `published_at`;
- `72h`: 72 hours after `published_at`;
- `7d`: 7 days after `published_at`;
- `final`: `config.final_after_days` after `published_at`.

The collector should not overwrite or update existing metric snapshots. Idempotency comes from deterministic dedupe keys:

```text
vk_api:{source_config_id}:{publication_id}:{owner_id}_{post_id}:{window}:{metric_name}
```

Repeated scheduled runs therefore skip snapshots that were already imported for the same publication/window/metric.

## Metrics

Sprint 48 records raw VK post counters only:

- `views`: from `post.views.count` when present;
- `likes`: from `post.likes.count` when present;
- `reposts`: from `post.reposts.count` when present;
- `comments`: from `wall.getComments(...).response.count`.

The collector does not record a derived engagement score in Sprint 48. Effectiveness views can derive engagement later from the raw counters.

Each snapshot should use:

- `source = "vk_api"`;
- `source_method = "vk_api.wall.getById"` for views, likes, and reposts;
- `source_method = "vk_api.wall.getComments"` for comments;
- `confidence = source_config.default_confidence`;
- `source_config_id` and `import_run_id`;
- `external_metric_id = "{owner_id}_{post_id}:{metric_name}"`;
- `raw_payload` containing a compact non-secret provider payload, including owner id, post id, VK method name, counter value, and response fragments needed for debugging.

## Services

Add a `VKMetricCollectorService` with small testable boundaries:

- `VKPostIdentity` parser for `platform_post_id` and `platform_post_url`.
- `VKMetricsClient` for VK HTTP calls.
- `VKMetricCollectorService.collect_for_source(...)` orchestration.
- A helper that resolves due metric windows and missing dedupe keys.

Collection flow:

1. Start a `cf_metric_import_run` with `triggered_by`.
2. Load eligible VK publications for the source.
3. Resolve VK post identities.
4. Fetch post counters through VK API.
5. Record metric snapshots through `MetricService.record_deduped`.
6. Finish the import run as:
   - `succeeded` when all eligible posts were processed without errors;
   - `partial` when at least one metric was created/skipped but some publications failed;
   - `failed` when no useful work was completed because configuration or VK API access failed.
7. Store counts and a compact `raw_summary` on the run.

## API

Add a manual run endpoint:

```http
POST /api/content-factory/metric-sources/{source_config_id}/run
```

Request body:

```json
{
  "publication_id": "optional uuid",
  "force": false
}
```

Behavior:

- Requires Content Factory access.
- Only supports `source = "vk_api"` in Sprint 48.
- `publication_id` limits the run to one publication.
- `force = false` uses dedupe and due-window rules.
- `force = true` is reserved for a future diagnostic/backfill mode. Sprint 48 should reject it with a readable `400` response to avoid implying that snapshots can be overwritten.
- Returns the completed `CFMetricImportRunResponse`.

## Scheduler

Add `ContentFactoryMetricImportSchedulerService` using the existing APScheduler pattern.

Default behavior:

- Runs every 30 minutes.
- Loads active `vk_api` metric source configs.
- Calls the collector with `triggered_by = "scheduled"`.
- Does nothing if no active VK metric source config exists.
- Logs failures but does not crash application startup.

Settings:

- `CF_METRIC_IMPORT_ENABLED: bool = true`
- `CF_METRIC_IMPORT_INTERVAL_MINUTES: int = 30`

The scheduler should be wired in `backend/app/main.py` and stopped on shutdown.

## Error Handling

Configuration errors:

- missing VK token;
- missing owner id when a post id needs owner fallback;
- invalid source config type;
- invalid post identity.

Provider errors:

- HTTP request failure;
- VK API `error` response;
- unexpected response shape;
- post not found.

Rules:

- Do not log access tokens.
- Store readable operator-facing errors on `cf_metric_import_run.error_message`.
- Store per-publication failures in `raw_summary.errors` with publication id and non-secret VK identity.
- Continue processing other publications when one publication fails.

## Frontend

Sprint 48 keeps frontend changes minimal:

- Add API client method for the manual run endpoint.
- Add type coverage for the run request if needed.
- Keep the existing publication metric history provenance display from Sprint 47.
- Do not add a new navigation item or full setup UI.

Manual QA can use the backend endpoint and then confirm imported metrics appear in publication metric history.

## Testing Strategy

Backend unit tests:

- VK post identity parser handles ids and URLs.
- Due-window resolver returns only due and configured windows.
- VK client maps successful responses and VK error responses.
- Collector records expected metric snapshots with source/import provenance and dedupe keys.
- Collector skips duplicate metrics on repeated runs.
- Collector marks runs as `partial` when some publications fail.
- Collector rejects missing token/owner configuration without leaking secrets.

Backend API tests:

- Manual run endpoint requires Content Factory access.
- Unsupported source returns a readable error.
- VK run returns a completed import run response.

Scheduler tests:

- Scheduler loads active `vk_api` sources and calls the collector.
- Scheduler does nothing when there are no active sources.
- Scheduler catches collector errors.

Frontend source guard:

- API client exposes the manual metric source run method.
- Metric history continues to show integration provenance.

## Definition of Done

- A configured active VK metric source can import metrics for published VK publications.
- Imported snapshots include source config, import run, external metric id, dedupe key, method, confidence, and compact raw payload.
- Re-running the same collector does not create duplicate snapshots.
- Import runs show found, created, skipped duplicate, and error counts.
- The scheduler can run the collector without a user click once a source config exists.
- Manual run endpoint exists for QA and operational recovery.
- Existing manual metric entry, paste import, publishing queue, Telegram publishing, and VK publishing tests remain green.
- Durable repo docs are updated with Sprint 48 status and test instructions.
