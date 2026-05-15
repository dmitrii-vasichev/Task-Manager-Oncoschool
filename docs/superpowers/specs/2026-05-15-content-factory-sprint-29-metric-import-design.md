# Content Factory Sprint 29 Metric Paste Import Design

## Context

Content Factory already supports metric snapshots and manual one-by-one metric entry. The market research recommends manual or semi-automated ledgers before fragile platform API integrations, especially for Telegram, VK, Max, Dzen, OK, GetCourse, and email channels.

The current gap is operational speed. If a user copies several rows from TGStat, VK, GetCourse, email dashboards, or a spreadsheet, they must re-enter every metric by hand.

## Goal

Let users paste multiple metric rows into the publication detail page, preview validation results, and save valid rows through the existing metric API.

## Scope

In scope:

- Frontend-only paste import on the existing `Метрики` panel.
- New `Импорт` action next to `Добавить метрику`.
- Dialog with a textarea for pasted rows.
- Supported row format: `window | metric name | value | source | confidence | note`.
- Delimiters: tab, semicolon, comma, or pipe.
- Defaults: source `import`, confidence `medium`, source method `paste import`.
- Russian and English aliases for metric windows, sources, and confidence.
- Numeric values with comma or dot decimals.
- Preview summary for ready and invalid rows.
- Invalid rows stay visible with readable error text.
- Saving valid rows sequentially through existing `api.recordCFMetric`.
- Reuse existing metric refresh callback after successful import.
- Source guards and helper tests.
- Durable documentation updates.

Out of scope:

- Backend bulk endpoint.
- File upload.
- XLSX parsing.
- Partial rollback if one API call fails.
- Automatic platform API collection.
- Metric deduplication.
- Editing or deleting existing metric rows.

## Input Format

Each non-empty row is parsed as:

```text
Окно | Метрика | Значение | Источник | Доверие | Заметка
24h | Просмотры | 1200 | TGStat | Высокое | экспорт из TGStat
7d | Регистрации | 34 | GetCourse | Среднее | ручной отчёт
```

The first row can be a header and will be ignored when it contains labels such as `window`, `окно`, `metric`, or `метрика`.

Valid metric windows:

- `3h`, `24h`, `72h`, `7d`, `final`, `custom`
- Russian aliases such as `3 часа`, `24 часа`, `72 часа`, `7 дней`, `финал`, `другое`

Valid sources:

- `manual`, `api`, `tgstat`, `telemetr`, `vk_api`, `email_provider`, `getcourse`, `parser`, `import`
- Common readable aliases such as `TGStat`, `VK`, `email`, `GetCourse`, `импорт`, `вручную`

Valid confidence values:

- `high`, `medium`, `low`
- Russian aliases `высокое`, `среднее`, `низкое`

## Frontend Design

Add a new component:

- `ContentFactoryMetricImportDialog`

The metric history header keeps the existing `Добавить метрику` button and adds `Импорт`.

The import dialog contains:

- Short format hint.
- Paste textarea.
- Preview block with counts: rows ready to save and rows with errors.
- Compact list of parsed rows.
- Error list for invalid rows.
- Save button that is disabled when no valid rows exist.

The dialog calls `api.recordCFMetric(publicationId, payload)` for every valid row. It closes only after all valid rows are saved, then calls `onImported`.

## Parsing Helpers

Add pure helpers to `frontend/src/lib/contentFactoryUtils.ts`:

- `parseContentFactoryMetricImportRows(input: string): ContentFactoryMetricImportPreview`

The preview includes:

- `rows`: all parsed non-header rows with line number, raw text, optional payload, and optional error.
- `validRows`: rows that have a payload.
- `invalidRows`: rows with an error.

This keeps parsing testable without mounting React components.

## Testing

Frontend helper tests:

- Parses pipe-delimited rows with Russian labels and numeric comma values.
- Skips a header row.
- Applies source/confidence defaults when columns are omitted.
- Reports readable errors for missing metric name, invalid window, and invalid numeric value.

Source guards:

- `ContentFactoryMetricImportDialog.tsx` exists.
- Metric history imports and renders the import dialog.
- Metric history exposes the `Импорт` action.
- Import dialog uses `parseContentFactoryMetricImportRows` and `api.recordCFMetric`.

Full verification:

- Focused content factory utility/source guard tests.
- Full frontend test suite.
- TypeScript, lint, build, and whitespace checks.
