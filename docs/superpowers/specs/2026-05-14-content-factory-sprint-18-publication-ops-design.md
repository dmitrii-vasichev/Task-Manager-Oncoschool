# Content Factory Sprint 18 Publication Operations Design

## Context

The Content Factory already stores channel-specific publications, planned and actual publication times, platform post links, UTM data, audience targets, and manual metric snapshots.

The current workflow can create and edit those records, but the operational moment is too hidden: a user opens one publication and has to infer whether it was actually published, whether a post link is missing, and whether there is any metric evidence.

Sprint 18 turns the existing fields into a clear publication operations surface.

## Goal

Add a focused `Публикация и статистика` panel to the publication detail page.

Users should be able to:

- See whether publication execution is still planned, already confirmed, missing a fact date, failed, or cancelled.
- Understand whether the platform is handled manually, by API, or by a mixed process.
- Save the publication fact without opening the large edit dialog.
- Store the external post URL and platform post ID.
- See whether metric evidence exists for the publication.

## Scope

In scope:

- Normalize platform `capabilities` JSON into readable operation labels.
- Derive publication operation state from existing `CFPublication`, `CFPlatform`, and `CFMetricSnapshot` records.
- Add a dedicated frontend panel on `/content-factory/publications/[id]`.
- Add source guards and focused helper tests.

Out of scope:

- Social network API integrations.
- Automatic publication.
- Automatic metric collection.
- New backend tables or migrations.
- Calendar drag-and-drop scheduling.
- Bulk publication creation.

## Platform Capabilities

The helper should support flexible capability keys because the reference dictionary stores JSON.

Supported meanings:

- Manual publication is enabled by default.
- Manual metric entry is enabled by default.
- Post URL storage is enabled by default.
- API publication and API metric collection are opt-in.

The UI should not expose raw JSON keys. It should render Russian labels such as `Ручная публикация`, `API-публикация`, `Смешанная публикация`, `Ручной сбор метрик`, and `API-метрики`.

## Publication Operations

The helper should return:

- `publishFactLabel`: concise state label.
- `missingPublishedAt`: true when status is published but actual publish time is empty.
- `missingPostUrl`: true when the publication is published, the platform can store a URL, and the URL is empty.
- `needsMetricEvidence`: true when a publication is published without any metrics.
- `metricEvidenceLabel`: Russian count label for metric snapshots.
- Normalized platform capabilities.

## UI

Place the panel in the publication detail sidebar above audience targeting and UTM.

The panel should show:

- Title: `Публикация и статистика`
- Status row for publication fact.
- Capability rows for publication and metrics.
- Post link / post ID state.
- Metric evidence count.
- A primary action:
  - `Отметить как опубликовано` when not yet published.
  - `Обновить факт публикации` when already published.

The action opens a compact dialog with:

- Actual publish datetime.
- Post URL.
- Platform post ID.

Saving should call the existing publication PATCH endpoint and set status to `published`.

## Risks

- Existing platforms may have no capability JSON. Defaults should keep the UI useful.
- Some teams may keep metrics manually for a long time. The UI should call this out as missing evidence, not as a hard error.
- The operation panel should complement, not duplicate, the larger publication edit dialog.

## Verification

Automated checks:

```bash
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryUtils.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```
