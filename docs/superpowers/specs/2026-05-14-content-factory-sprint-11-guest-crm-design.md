# Content Factory Sprint 11 Guest CRM Foundation Design

## Context

The preserved Content Factory research identifies patient and guest sourcing as a specialized workflow, not just another publication type. A patient live event or guest story needs sourcing, screening, consent, preparation, publication, gift delivery, and follow-up. If this work is stored only as a normal publication, the team loses consent state, allowed channels, anonymity boundaries, sensitive topics, legal notes, and the operational owner for each stage.

Sprint 1 and Sprint 2 already created the backend foundation for bundles, publications, audiences, metrics, retrospectives, and dictionaries. Sprint 3 through Sprint 10 made those resources usable in the frontend. The base content operations layer is now stable enough to add the first patient/guest CRM primitive.

## Goal

Add a backend foundation for patient and guest stories inside Content Factory:

- A dedicated `cf_guest_story` table.
- Pydantic request and response schemas.
- A service layer for create, read, list, and update operations.
- REST endpoints under `/api/content-factory/guests`.
- Tests for model registration, schema validation, service behavior, endpoint behavior, permissions, and migration shape.

This sprint should make the future frontend page possible without inventing UI behavior before the data contract is stable.

## Non-Goals

- Do not build the frontend guest CRM workspace in this sprint.
- Do not store uploaded consent documents or files.
- Do not implement digital signature flows.
- Do not integrate Google Forms, Typeform, Tally, GetCourse, Telegram, email, or legal-document providers.
- Do not add hard delete endpoints.
- Do not add AI drafting or patient-story rewriting.
- Do not store detailed medical records; keep notes operational and editorial.

## Data Model

Create `CFGuestStory` mapped to `cf_guest_story`.

Core identity and workflow fields:

- `id`: UUID primary key.
- `display_name`: internal guest or candidate display name.
- `contact_ref`: optional contact pointer such as Telegram handle, CRM link, or form response reference.
- `role`: `patient`, `relative`, `doctor`, `volunteer`, `partner`, or `other`.
- `source`: `manual`, `open_call`, `referral`, `screening_form`, `partner`, or `other`.
- `source_notes`: optional free-text source details.
- `story_brief`: short editorial summary of the story.
- `status`: guest pipeline stage.
- `owner_id`: required responsible team member.
- `stage_due_at`: optional next-stage deadline.

Content Factory links:

- `nosology_id`: optional link to `cf_nosology`.
- `bundle_id`: optional link to `cf_bundle`, using `ON DELETE SET NULL`.
- `publication_id`: optional link to `cf_publication`, using `ON DELETE SET NULL`.

Screening and quality-gate fields:

- `screening_notes`: producer/editorial screening notes.
- `medical_factcheck_notes`: factcheck notes for claims and medical boundaries.
- `rejection_reason`: reason when a candidate is rejected or deferred.

Consent and boundary fields:

- `consent_status`: `not_started`, `sent`, `signed`, `declined`, `revoked`, or `expired`.
- `consent_version`: optional template/version identifier.
- `consent_signed_at`: optional timestamp.
- `allowed_channels`: JSON list for allowed publishing channels.
- `anonymity_level`: `full_name`, `first_name`, `anonymous`, or `pseudonym`.
- `sensitive_topics`: JSON list of boundaries.
- `legal_notes`: legal/editorial notes.

Post-publication fields:

- `gift_status`: `not_required`, `pending`, `sent`, or `received`.
- `follow_up_due_at`: optional follow-up deadline.
- `created_at` and `updated_at`: timezone-aware timestamps.

Indexes:

- `status`
- `owner_id`
- `bundle_id`
- `publication_id`
- `stage_due_at`

## API

Add `backend/app/api/content_factory/guests.py`.

Endpoints:

- `GET /api/content-factory/guests`
  - Filters: `status`, `owner_id`, `consent_status`, `bundle_id`, `publication_id`, `limit`, `offset`.
  - Sort: nearest `stage_due_at` first, nulls last, then newest `created_at`.
- `POST /api/content-factory/guests`
  - Creates a guest story.
- `GET /api/content-factory/guests/{guest_story_id}`
  - Returns a guest story or `404`.
- `PATCH /api/content-factory/guests/{guest_story_id}`
  - Partially updates supported fields or returns `404`.

All endpoints require `require_cf_access`. Admin-only access is not appropriate because producers and editors need to manage guest pipelines.

## Error Handling

- Missing guest story reads and updates return `404` with Russian user-facing detail.
- Pydantic validates controlled enum-like values through `Literal` types.
- The service returns `None` for missing update targets and leaves HTTP mapping to the API layer.
- The API commits only after successful create or update.

## Testing

Use TDD before production code:

- Model test: `CFGuestStory` exists, uses `cf_guest_story`, exposes workflow/consent fields, and SQLAlchemy mappers configure.
- Schema tests: create payload defaults to `status="sourced"`, `consent_status="not_started"`, `anonymity_level="full_name"`, `gift_status="not_required"`, and rejects invalid controlled values.
- Service tests: create maps fields and list applies filters; update changes only provided fields.
- API tests: list/create/get/update call the service, commit on writes, and return `404` for missing reads/updates.
- Migration test: revision `042_content_factory_guest_story` creates `cf_guest_story` with required consent and workflow columns.

Validation commands:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_guest_stories_api.py tests/test_cf_guest_story_service.py tests/test_content_factory_models.py tests/test_content_factory_schemas.py -q
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_guest_story_migration.py -q
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_guest_stories_api.py tests/test_cf_guest_story_service.py tests/test_content_factory_models.py tests/test_content_factory_schemas.py tests/test_content_factory_guest_story_migration.py -q
git diff --check
```

## Future Work

The next frontend sprint can add a Russian workspace such as `Гости и истории` with pipeline filters, consent state, due dates, linked campaigns/publications, and help text. Later backend work can add intake-form imports, consent-document storage, reminders, and gift delivery confirmation once the team validates the manual workflow.
