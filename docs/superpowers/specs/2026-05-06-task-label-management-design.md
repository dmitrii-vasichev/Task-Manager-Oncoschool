# Task Label Management Design

## Metadata

| Field | Value |
| --- | --- |
| Date | 2026-05-06 |
| Status | Ready for user review |
| Feature | Task label color selection, editing, archiving, and moderator cleanup |
| Scope | Web portal task labels only |

## Problem

Task labels already exist in the portal as lightweight team-wide tags. Users can create labels while creating or editing tasks, and labels already store `color`, `created_by_id`, and `is_archived`. The current implementation does not let users choose a color, fix a label name, archive labels, or let moderators clean up the shared label catalog.

The next step is to make labels manageable without turning them into a separate project/workspace system.

## Goals

- Let users choose a label color from a fixed palette when creating a label.
- Let label creators edit or archive their own labels while the labels are still private to their own task context.
- Let moderators and admins edit, archive, and restore any label.
- Keep archived labels visible on old tasks, but hide them from normal picker/search results.
- Prevent automatic reactivation of archived labels by ordinary creation flows.
- Add a moderator-facing label management panel in Settings.
- Keep task visibility and task edit permissions unchanged.

## Non-Goals

- No hard delete of labels.
- No automatic removal of archived labels from existing tasks.
- No label merge or bulk relabeling workflow.
- No personal label page for ordinary members.
- No free-form color picker or arbitrary hex colors.
- No Telegram bot label management in this iteration.
- No analytics by label in this iteration.

## Chosen Approach

Use a two-tier management model:

- Ordinary members manage only their own active labels directly from `TaskLabelPicker`, and only while those labels have not become shared.
- Moderators and admins manage the full label catalog from a new `Settings -> Task labels` tab.
- A moderator shortcut from `TaskLabelPicker` opens `/settings?tab=task-labels`.

This keeps member workflows close to task editing while giving moderators a dedicated cleanup surface for shared taxonomy work.

## Key Product Rules

### Label Ownership

A label is owned by the team member stored in `TaskLabel.created_by_id`. Labels with a null owner are treated as moderator-managed labels for member permission purposes.

### Shared Label Detection

For an ordinary member, a label is shared if it is attached to at least one task where either:

- `task.created_by_id` is null or different from the current member id, or
- `task.assignee_id` is null or different from the current member id.

Only labels that are owned by the current member and are not shared are editable or archivable by that member.

### Archiving

Archiving is a soft delete:

- Set `task_labels.is_archived = true`.
- Keep existing `task_label_links` unchanged.
- Continue returning archived labels inside task responses for tasks that already have them.
- Exclude archived labels from normal autocomplete, creation pickers, and task label filters.
- Allow restore only for moderators and admins.

### Archived Name Conflict

If a user creates a label whose normalized slug already exists in the archive, the API must not reactivate it automatically. It should return a conflict response explaining that a moderator can restore the archived label.

## Color Palette

Labels use a fixed backend-validated palette. The initial palette should be compatible with the existing chip styling and both light and dark themes:

- `teal`
- `blue`
- `purple`
- `gold`
- `green`
- `coral`
- `rose`
- `slate`

The backend rejects unknown color keys. If a client omits `color` during creation, the backend may keep the existing deterministic color fallback so older clients continue to work.

## API Design

### Response Shape

Extend `TaskLabelResponse` with capability fields computed for the current user:

| Field | Type | Notes |
| --- | --- | --- |
| `can_edit` | boolean | True when the current user can update name/color |
| `can_archive` | boolean | True when the current user can archive the active label |
| `can_restore` | boolean | True for moderators/admins on archived labels |
| `is_shared_for_current_user` | boolean | True when member-level ownership controls are blocked by shared usage |

Existing fields remain: `id`, `name`, `slug`, `color`, `created_by_id`, `is_archived`, timestamps, and `usage_count`.

### `GET /api/task-labels`

Query parameters:

- `search`: optional normalized text search.
- `limit`: default 20, bounded as today.
- `include_archived`: default false.

Behavior:

- Ordinary users can request only active labels. `include_archived=true` returns `403`.
- Moderators/admins can request active and archived labels.
- The normal picker keeps using active-only results.
- The moderator Settings tab uses `include_archived=true` when showing archived labels.
- Usage counts remain scoped to the current user's visible task universe for normal users. Moderators/admins see company-wide counts.

### `POST /api/task-labels`

Request:

```json
{
  "name": "Conference",
  "color": "teal"
}
```

Behavior:

- Normalize and validate `name`.
- Validate `color` against the fixed palette when present.
- If an active label with the same slug exists, return that active label, preserving existing deduplication behavior.
- If an archived label with the same slug exists, return `409 Conflict`.
- Otherwise create the label with `created_by_id` set to the current member.

### `PATCH /api/task-labels/{id}`

Request:

```json
{
  "name": "Conference 2026",
  "color": "purple"
}
```

Behavior:

- Allows partial update of `name` and/or `color`.
- Requires moderator/admin or member ownership of an active, non-shared label.
- Rejects unknown labels with `404`.
- Rejects archived labels for ordinary members with `403`.
- Rejects duplicate normalized names with `409`, including conflicts against archived labels.
- Updates `slug` when `name` changes.

### `DELETE /api/task-labels/{id}`

Behavior:

- Soft archives the label.
- Requires moderator/admin or member ownership of an active, non-shared label.
- Does not delete `task_label_links`.
- Returns the updated label response with `is_archived = true`.

### `POST /api/task-labels/{id}/restore`

Behavior:

- Moderator/admin only.
- Sets `is_archived = false`.
- Returns the restored label response.
- Ordinary members receive `403`.

## Backend Components

- Add `TaskLabelUpdate` schema with optional `name` and `color`.
- Extend `TaskLabelCreate` with optional `color`.
- Add palette validation in the schema layer or repository/service boundary.
- Replace `create_or_reactivate` behavior with create-or-return-active plus archived-conflict handling.
- Add repository helpers:
  - `get_by_id`
  - `update`
  - `archive`
  - `restore`
  - `is_shared_for_member`
  - capability calculation for current user
- Keep task label replacement from attaching missing labels; also exclude archived labels from being newly attached unless the label is already present on that task and the request is preserving it.
- Keep archived labels loaded in task responses with `selectinload(Task.labels)` so historical context remains visible.

## Frontend UX

### Label Picker

`TaskLabelPicker` remains the main member workflow:

- Creation flow shows a compact fixed color palette next to the new label action.
- Label rows show color swatches.
- Labels with `can_edit` or `can_archive` show compact row actions.
- Edit opens a small dialog or inline editor for name and palette color.
- Archive uses confirmation text: "This label will stay on old tasks but will no longer be available for new tasks."
- If the backend returns `403` or `409`, show a toast and refresh label results.
- Moderator/admin users see a "Manage labels" link to `/settings?tab=task-labels`.

### Task Chips

`TaskLabelChips` keeps using palette keys for chip styling. Add a class for `rose` and keep `slate` as the fallback for unknown legacy values.

### Settings Panel

Add a new `task-labels` tab to `/settings`, visible to moderators/admins.

The `TaskLabelsSection` shows:

- Search field.
- Active/Archived segmented filter.
- Label name.
- Color swatch.
- Usage count.
- Owner name resolved from team members when available.
- Status.
- Row actions.

Active labels support edit and archive. Archived labels support restore. Empty, loading, and error states should match existing Settings sections.

## Error Handling

- `400`: invalid label name or invalid color.
- `403`: current user cannot perform the action.
- `404`: label does not exist.
- `409`: normalized name conflicts with an archived label or with another active label during update.

Frontend copy should be user-facing and specific:

- "This label is already archived. Ask a moderator to restore it."
- "This label is now shared with other tasks, so only a moderator can change it."
- "Choose one of the available label colors."

## Data Flow

1. User opens a task label picker.
2. Picker fetches active labels and receives capability flags.
3. User creates a label with `name` and `color`.
4. Backend validates, creates or returns an active duplicate, and responds with capabilities.
5. User attaches labels to a task through existing task create/edit payloads.
6. If a label is later attached to another person's task context, member capabilities for that label turn false on the next fetch.
7. Moderator manages shared or archived labels from Settings.

## Testing Plan

### Backend

- Creating a label accepts valid palette colors.
- Creating a label rejects invalid palette colors.
- Creating a label with an archived slug returns `409`.
- Creating a label with an active slug returns the existing active label.
- Member can update and archive an owned, active, non-shared label.
- Member cannot update or archive a label they do not own.
- Member cannot update or archive an owned label once it is shared.
- Null task author or assignee makes a member-owned label shared for that member.
- Moderator/admin can update and archive any label.
- Moderator/admin can restore archived labels.
- Ordinary member cannot request `include_archived=true`.
- Archived labels are excluded from normal label search.
- Archived labels remain present in existing task responses.
- Archived labels cannot be newly attached to tasks through `label_ids`.

### Frontend

- TypeScript check passes.
- Label picker renders color choices during create.
- Label picker shows edit/archive actions only when capability flags allow them.
- Label picker shows the moderator management link only for moderators/admins.
- Settings tab renders active and archived label states.
- Settings actions handle `403` and `409` responses with toasts and refresh.
- Chip styling supports all palette keys.

### Manual Smoke

- Create a label with a selected color.
- Edit name and color for an owned, non-shared label.
- Archive an owned, non-shared label and confirm it disappears from picker results.
- Confirm the archived label remains visible on a task that already had it.
- As moderator, view active and archived labels in Settings.
- As moderator, restore an archived label and confirm it returns to picker results.

## Documentation Updates During Implementation

- Update `docs/PLAN.md` with the implementation tasks and validation commands.
- Update `docs/STATUS.md` as implementation progresses.
- Update `docs/TEST_PLAN.md` with the backend and frontend validation checklist.

## Open Decisions

No open product decisions remain for the first implementation pass. Merge/bulk cleanup and analytics are intentionally deferred.
