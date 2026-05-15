# Content Factory Sprint 43 Planning Matrix Design

## Goal

Add a campaign-level cross-channel planning matrix that makes the campaign plan visible without introducing a new backend workflow.

## Product Context

Sprint 42 moved spreadsheet-like publication plans into Content Factory through a safe table import. The next gap is campaign-level visibility: users can create individual publications, but they still need a quick way to see whether a campaign has the expected channel coverage from its funnel template.

## Scope

Sprint 43 is frontend-only. It reuses:

- `cf_bundle.funnel_template_id` as the source of expected publication recipes.
- `cf_funnel_template.template_publications` as the expected format/platform/date offsets.
- Existing `cf_publication` records as the source of truth.
- Existing publication create API for quick creation of missing channel items.

No new backend schema, endpoint, or queue is added in this sprint.

## User Experience

On the campaign detail page, above the publication list, users see `Матрица каналов`.

The matrix shows:

- expected publication count;
- created publication count;
- missing publication count;
- publications that exist in the campaign but are outside the selected template;
- rows from the funnel template, with planned dates derived from the campaign event date;
- columns for the platforms required by the template;
- existing publication cards linked to publication detail;
- `Создать` actions for missing cells.

If the campaign has no event date, the matrix still shows required channel items but labels planned dates as unavailable. If the template references an unknown platform or format, the matrix shows a warning and skips that invalid slot.

## Data Rules

Each template publication may define:

- `format_code`
- `default_platforms`
- `platform_code`
- `offset_days`
- `offset_hours`
- `title`
- `label`

The helper resolves format/platform codes through the current reference dictionaries. It creates one expected cell per format/platform pair.

Existing publications are matched by `platform_id` and `format_id`. When a slot has a planned date, the closest scheduled publication is matched first so duplicate formats such as early and late `follow_up` can still be represented.

Missing cells create draft publications with:

- campaign id from the current bundle;
- platform and format from the matrix cell;
- responsible user from the campaign owner;
- planned date from the cell;
- draft status;
- UTM markers `cf_planning_matrix_source` and `cf_planning_matrix_slot`.

## Validation

Automated coverage:

- helper tests for matrix slot building, matching, missing cells, warnings, and summary counts;
- source guard for campaign page wiring, matrix UI copy, quick-create API call, and planning UTM markers;
- full frontend tests, TypeScript, lint, build, and diff check.

Manual QA:

- open a campaign with a funnel template;
- confirm expected rows and platform columns;
- create a missing cell;
- confirm the new draft publication appears in the matrix and publication list;
- open the created publication and confirm platform, format, schedule, owner, draft status, and UTM markers.
