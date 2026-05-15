# Content Factory Sprint 32 Saved Publication Variants Design

## Context

Sprint 31 added deterministic channel adaptations on publication detail pages. Users can now copy Telegram, VK, email, push, Max, and Dzen versions, but those edits disappear after the copy step. The production workflow still needs a durable place where the team can revise, save, return to, and copy the final channel-specific text.

## Goal

Add saved publication variants as a first durable layer for channel-specific copy.

Users should be able to open a publication, pick a channel adaptation, edit the title/body/notes, save it, refresh the page, and continue from the saved version.

## Scope

- Backend table `cf_publication_variant`.
- Backend schemas for variant responses and upsert payloads.
- Publication service methods for listing variants and upserting one variant per publication/channel.
- REST endpoints under `/api/content-factory/publications/{publication_id}/variants`.
- Frontend types and API client methods.
- Publication detail data loading for variants.
- Update `ContentFactoryPublicationVariants` from copy-only preview to editable saved drafts.
- Backend, frontend source guard, and focused helper/UI tests.
- Durable plan/status/test docs.

## Non-Goals

- No AI generation.
- No multi-version history for variants.
- No approval workflow per variant.
- No external platform publishing API.
- No collaborative locking or comments.
- No delete/archive endpoint in this sprint.

## Data Model

`cf_publication_variant` stores one row per publication/channel:

- `id`;
- `publication_id`;
- `channel`;
- `title`;
- `body_text`;
- `notes`;
- `source_version_number`;
- `updated_by_id`;
- `created_at`;
- `updated_at`.

The unique key is `(publication_id, channel)`. The allowed channels are `telegram`, `vk`, `email`, `push`, `max`, and `dzen`.

`source_version_number` records the publication body version used when the variant was last saved. It gives the UI a lightweight signal that a saved adaptation may have been based on an older publication version.

## API

Add endpoints:

- `GET /api/content-factory/publications/{publication_id}/variants`
- `PUT /api/content-factory/publications/{publication_id}/variants/{channel}`

`GET` returns saved variants ordered by channel. `PUT` creates or updates the variant for the selected channel. If the publication does not exist, `PUT` returns 404.

## UX

The existing `Адаптации` panel remains below `Пакет для публикации`.

The panel becomes an editor:

- channel selector stays visible;
- if a saved variant exists, fields are filled from the saved row;
- if no saved variant exists, fields start from the deterministic Sprint 31 draft;
- users can edit title, body, and internal notes;
- `Сохранить адаптацию` persists the selected channel;
- `Скопировать адаптацию` copies the current editor text;
- the panel shows whether the selected channel is already saved and which publication version it came from.

The UI stays operational and compact, with readable Russian labels. It should feel like a production desk, not an AI console.

## Testing

Automated tests cover:

- model and schema existence;
- migration creates the table, unique key, and indexes;
- service upsert creates and updates one row per publication/channel;
- API list/upsert endpoints delegate correctly and return 404 when the publication is missing;
- frontend types and API client expose variant methods;
- publication detail route loads variants and passes them to the adaptations component;
- component source guard confirms editable fields, save action, copy action, and `api.upsertCFPublicationVariant`.

Manual QA:

1. Open a publication detail page.
2. Select Telegram in `Адаптации`.
3. Edit title, body, and notes.
4. Save the adaptation.
5. Refresh the page and confirm the saved text is still there.
6. Switch to another channel and confirm it starts from the generated draft until saved.
7. Copy the edited adaptation and confirm pasted text uses the edited fields.
