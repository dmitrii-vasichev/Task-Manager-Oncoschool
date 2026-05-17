# Content Factory Sprint 47 Metrics Integration Foundation Design

## Goal

Sprint 47 creates the backend and lightweight frontend foundation for automated Content Factory metric collection.

The sprint does not connect a real external metric API yet. It makes future collectors safe by giving them durable source configuration, import-run audit records, freshness/error state, metric provenance, and deduplication rules. Sprint 48 can then add the first real collector without inventing these concepts inside one platform-specific service.

## Context

Content Factory already supports manual and paste-imported metric snapshots. Those snapshots power publication metric insights, effectiveness analytics, audience analytics, readiness checks, retrospectives, and help content.

Wave D now starts metric automation. The roadmap says Sprint 47 should add:

- metric source configuration,
- import runs,
- source freshness,
- confidence labels,
- deduplication rules,
- visible integration errors,
- continued support for manual and paste-imported metric snapshots.

The current `cf_metric_snapshot` table has source, source method, confidence, raw payload, and note fields, but it does not know which configured integration produced a metric, which collection run produced it, whether a duplicate was skipped, or whether a source is stale/failing.

## Scope

In scope:

- Add metric source configuration records.
- Add metric import run records.
- Extend metric snapshots with optional source config, import run, external metric id, and dedupe key fields.
- Add backend services for source configuration, run lifecycle, and deduplicated metric recording.
- Add Content Factory API endpoints for listing and managing metric source configurations and reading import runs.
- Keep existing manual metric capture and paste import behavior valid.
- Add frontend types and API methods for metric source configs and import runs.
- Add lightweight metric-history provenance display for integration-produced metric snapshots.
- Update durable docs and tests.

Out of scope:

- Calling VK, Telegram, TGStat, Telemetr, GetCourse, email provider, or parser APIs.
- Storing raw access tokens or secrets in Content Factory tables.
- Building a full credentials UI.
- Scheduling background metric collection jobs.
- A new top-level Content Factory navigation item.
- Editing or deleting metric snapshots.
- Recalculating old effectiveness analytics from raw payloads.

## Data Model

### Metric Source Config

Add `cf_metric_source_config`.

Fields:

- `id`
- `source`: one of the existing metric source codes, such as `vk_api`, `getcourse`, `tgstat`, `telemetr`, `email_provider`, `parser`, or `api`.
- `name`: operator-facing name, such as `VK community wall` or `GetCourse registrations`.
- `description`
- `is_active`
- `freshness_window_hours`: how long a successful run remains considered fresh.
- `default_confidence`: default confidence assigned to snapshots created by this source.
- `config`: non-secret JSON configuration, such as account id, community id, report kind, or metric mapping names.
- `credentials_ref`: an optional reference to a secret stored outside the table. The table must not store API tokens.
- `last_run_at`
- `last_success_at`
- `last_error_at`
- `last_error_message`
- `created_by_id`
- timestamps.

The table is intentionally generic. Platform-specific collectors should interpret `config` through their own service code, not through dynamic execution.

### Metric Import Run

Add `cf_metric_import_run`.

Fields:

- `id`
- `source_config_id`
- `status`: `pending`, `running`, `succeeded`, `failed`, or `partial`
- `triggered_by`: `manual`, `scheduled`, `system`, or `test`
- `requested_by_id`
- `started_at`
- `finished_at`
- `found_count`
- `created_count`
- `skipped_duplicate_count`
- `error_count`
- `error_message`
- `raw_summary`
- timestamps.

Runs are append-only audit evidence. Future collectors should create a run, record created/skipped/error counts, and close the run with success, partial success, or failure.

### Metric Snapshot Provenance

Extend `cf_metric_snapshot` with:

- `source_config_id`
- `import_run_id`
- `external_metric_id`
- `dedupe_key`

Manual and paste-imported metrics can leave all four fields empty. Integration-created metrics should include at least `source_config_id`, `import_run_id`, and `dedupe_key`; `external_metric_id` is optional because some reports do not expose stable row ids.

## Deduplication Rule

Deduplication is opt-in through `dedupe_key`.

If a metric create payload has no `dedupe_key`, `MetricService.record` keeps current behavior and always creates a new snapshot. This protects manual entry and paste import.

If a metric create payload has a `dedupe_key`, the service checks for an existing metric snapshot with the same key:

- If one exists, the service returns the existing snapshot and marks the operation as skipped duplicate in the service result.
- If none exists, the service creates a new snapshot.

Collectors should build stable keys from:

- source config id,
- publication id,
- metric window,
- metric name,
- external metric id when available,
- otherwise a normalized source-specific period/report identifier.

The database should enforce uniqueness for non-null dedupe keys to protect against race conditions.

## Backend Services

### MetricSourceConfigService

Responsibilities:

- create source config,
- update source config,
- list source configs with optional active/source filters,
- get source config by id,
- update cached run state after import runs finish.

Validation:

- `name` must not be blank.
- `source` must use an existing metric source code.
- `freshness_window_hours` must be positive.
- `credentials_ref` may be blank/null, but API tokens must not be accepted in `config`.

### MetricImportRunService

Responsibilities:

- start a run for a source config,
- mark a run succeeded, failed, or partial,
- update source config `last_run_at`, `last_success_at`, `last_error_at`, and `last_error_message`,
- list recent runs, optionally filtered by source config and status.

Sprint 47 exposes run listing through API. Run creation and closing can be service-level only until Sprint 48 adds real collectors.

### MetricService

Responsibilities added in Sprint 47:

- accept provenance fields in `CFMetricSnapshotCreate`,
- support dedupe-aware recording,
- preserve the existing `record` return shape for current API handlers,
- expose a new result object for integration services that need to know whether a snapshot was created or skipped.

The existing publication metric POST endpoint should keep returning a metric snapshot. It should not expose duplicate-skip behavior to manual users because manual users do not send dedupe keys.

## API

Add routes under `/api/content-factory`.

Metric source configs:

- `GET /metric-sources`
- `POST /metric-sources`
- `GET /metric-sources/{source_config_id}`
- `PATCH /metric-sources/{source_config_id}`

Import runs:

- `GET /metric-import-runs`
- `GET /metric-sources/{source_config_id}/import-runs`

Access:

- same Content Factory access gate as other operational endpoints.
- no admin-only gate in Sprint 47 because metric source visibility is operational. If real credential management is added later, secret mutation can become admin-only.

## Frontend

Sprint 47 should avoid adding another top-level navigation item. Content Factory already has many sections, and this sprint is mostly foundation.

Add:

- `CFMetricSourceConfig` and `CFMetricImportRun` frontend types.
- API client methods for metric sources and import runs.
- Metric history provenance display:
  - source config name when available,
  - run status/id hint for integration-created metrics,
  - external metric id when available,
  - dedupe key presence as an audit hint, not as a primary user label.

Publication detail can fetch metric source configs once and pass them into the metric history component. If source loading fails, the metric history should still render using existing metric labels.

## Error Handling

Operator-facing errors:

- metric source not found,
- metric source name is empty,
- freshness window must be positive,
- import run cannot be completed from a terminal state,
- duplicate metric was skipped by service-level result, not treated as a user-facing error.

Internal safety:

- do not store secrets in `config`,
- do not log or return secret-looking values,
- do not block existing metric capture when source config/run lookup fails on the frontend.

## Testing

Backend tests:

- model tests for new tables and snapshot provenance fields.
- schema tests for source config, import run, and metric snapshot provenance fields.
- service tests for source create/update/list and run lifecycle.
- service tests for dedupe-aware metric recording.
- API tests for metric source config list/create/update and import run list endpoints.
- regression test that manual metric recording still creates new snapshots without dedupe keys.

Frontend tests:

- source guard for new API client methods and types.
- source guard that publication detail fetches metric source configs.
- source guard that metric history renders source config/provenance labels without replacing existing manual metric history behavior.

Full verification:

- focused backend tests for metric foundation.
- full backend `pytest -q`.
- frontend source guard.
- full frontend tests, TypeScript, lint, build.
- `git diff --check`.

## Manual QA

1. Open a publication detail page with existing manual metrics and confirm the metric history still renders.
2. Add a manual metric and confirm it saves as before.
3. Paste-import metric rows and confirm they save as before.
4. Create a metric source config through API or dev tooling.
5. Confirm `GET /api/content-factory/metric-sources` returns the source without secret values.
6. Create or simulate an import run in tests/dev tooling and confirm `GET /api/content-factory/metric-import-runs` returns status, counts, and error state.
7. Record an integration-style metric with a dedupe key and confirm a second identical call does not create a duplicate snapshot.
8. Open a publication detail page containing an integration-style metric and confirm the history shows readable source/provenance evidence.

## Follow-Up Sprint 48

Sprint 48 should choose the first real metric collector based on account access and API feasibility. Likely candidates:

- VK metrics for VK wall posts already published by Sprint 46.
- GetCourse registration/conversion metrics tied to campaign UTM.
- Telegram statistics through an available provider or exported report source.

The first collector should reuse `cf_metric_source_config`, `cf_metric_import_run`, `source_config_id`, `import_run_id`, and `dedupe_key` instead of adding platform-specific audit tables.
