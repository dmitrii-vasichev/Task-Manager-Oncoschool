# Content Factory Sprint 14 Guest Activity Design

## Context

Sprint 11 added the guest story backend entity, Sprint 12 added the guest list/create/edit workspace, and Sprint 13 added a readable guest story detail page. The next missing piece is memory: the team can see the current state, but not how the story got there or who added context.

The existing product already has task updates, idea events, and project events. Sprint 14 should add the same kind of lightweight operational history for guest stories without turning the workflow into a heavy automation engine.

## Goal

Add a guest story activity journal.

Content Factory users should be able to:

- See a chronological activity list on `/content-factory/guests/[id]`.
- Add a manual team comment to a guest story.
- See automatic events when key fields change:
  - pipeline stage;
  - consent state;
  - gift state;
  - follow-up date.
- See who created the activity item and when it happened.

## Non-Goals

- Do not add reminders or scheduled notifications.
- Do not add file uploads or consent document storage.
- Do not add threaded comments, reactions, editing, or deleting activity items.
- Do not expose arbitrary system event creation from the frontend.
- Do not build a separate activity route; activity belongs on the guest detail page.

## Backend Design

Add `cf_guest_story_event`.

Fields:

- `id`
- `guest_story_id` with cascade delete
- `actor_id` nullable team member reference
- `event_type`
- `body`
- `old_value`
- `new_value`
- `payload` JSONB object
- `created_at`

Event types:

- `created`
- `comment`
- `status_changed`
- `consent_changed`
- `gift_changed`
- `follow_up_changed`

Add schemas:

- `CFGuestStoryEventCreate`
- `CFGuestStoryEventResponse`

Add service methods:

- `list_events(session, guest_story_id)`
- `create_event(...)`
- `create_comment(session, guest_story_id, actor_id, body)`

Update `GuestStoryService.create` to create a `created` event when `actor_id` is provided.

Update `GuestStoryService.update` to compare watched fields before applying updates and create automatic events when values change. Existing callers can omit `actor_id`; the API should pass the current member id.

Add API endpoints:

- `GET /api/content-factory/guests/{guest_story_id}/events`
- `POST /api/content-factory/guests/{guest_story_id}/events`

The POST endpoint creates a manual comment only.

## Frontend Design

Add frontend types and API methods:

- `CFGuestStoryEventType`
- `CFGuestStoryEvent`
- `CFGuestStoryEventCreateRequest`
- `api.getCFGuestStoryEvents(guestStoryId)`
- `api.createCFGuestStoryEvent(guestStoryId, data)`

Add `ContentFactoryGuestActivityPanel`.

The panel should:

- render events newest-first;
- show clear Russian labels for event types;
- show actor names using loaded team members;
- show old/new values for automatic changes;
- include a compact textarea and button for manual comments;
- refresh the detail page activity list after a comment is created.

Update `/content-factory/guests/[id]` to load events and pass them to the panel. Reference-data failures should not prevent the story from rendering; activity load failure should show an empty activity state and a toast.

## Error Handling

- Empty comment body should be blocked client-side.
- Backend should reject blank comment bodies through Pydantic validation.
- Missing guest story should return 404 for list/create event endpoints.
- Activity list failure should not blank the guest detail page.
- Automatic event creation should happen in the same transaction as the guest update.

## Testing

Backend:

- Model test for `CFGuestStoryEvent` table and mapper relationship.
- Schema test for event create/response.
- Service tests for manual comments and automatic change events.
- API tests for list, create, and 404 behavior.
- Migration source test for table, indexes, foreign keys, and downgrade.

Frontend:

- Type/API source guards for event contracts.
- Source guard for `ContentFactoryGuestActivityPanel`.
- Source guard that guest detail route loads and renders activity.

Validation commands:

```bash
cd backend && env PYTHONPATH=$PWD DEBUG=true BOT_TOKEN=123456:TEST DATABASE_URL=postgresql+asyncpg://cfuser:cfpass@localhost:5434/oncoschool_cf OPENAI_API_KEY=test pytest tests/test_content_factory_guest_stories_api.py tests/test_cf_guest_story_service.py tests/test_content_factory_models.py tests/test_content_factory_schemas.py tests/test_content_factory_guest_story_migration.py -q
cd frontend && node --test --experimental-strip-types src/lib/contentFactoryApiSourceGuards.test.ts src/components/content-factory/contentFactorySourceGuards.test.ts
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

## Future Work

Later sprints can turn activity into richer stage history, reminder automation, intake-form import history, consent-document audit links, and gift delivery tracking.
