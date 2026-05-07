# Meeting Board and AI Outcomes Design

## Summary

The meetings module should support a focused task-driven board for live Zoom calls and a separate post-meeting AI outcomes workflow.

The approved direction is not a full live collaborative workspace. It is a smaller, safer feature set:

- a shareable meeting board opened from a meeting page and shown during the call;
- hybrid task context pulled from meeting participants plus manually added people, departments, and pinned tasks;
- manual-only audio transcription after the meeting;
- AI-generated outcome drafts that moderators review before anything is saved as final work.

The goal is to help the team run meetings from portal tasks without forcing every participant to change tools immediately, while also improving meeting summaries and task extraction by replacing low-quality Zoom text transcripts with OpenAI transcription from Zoom audio.

## Goals

- Add a separate board surface that can be shared in Zoom during a meeting.
- Automatically seed the board from tasks owned by meeting participants.
- Let moderators add people, departments, and individual tasks to the board context.
- Show a clear task-focused meeting view: urgent work, in-progress work, review work, and tasks completed during the recent period.
- Let moderators attach lightweight meeting materials such as links and short notes.
- Keep the board connected to live portal tasks instead of copying tasks into meeting-specific records.
- Add manual post-meeting audio transcription from Zoom cloud recordings.
- Use OpenAI `gpt-4o-mini-transcribe` as the default transcription model for the first release.
- Never persist Zoom audio files in the portal.
- Generate editable AI drafts for summary, decisions, and new task candidates.
- Require moderator confirmation before saving decisions or creating tasks.

## Non-Goals

- No automatic task creation from AI output.
- No automatic transcription for every meeting in the first release.
- No persistent storage of Zoom audio files.
- No speaker diarization in the first release.
- No full live collaborative document editor.
- No real-time AI minutes during the call.
- No automatic updates to existing tasks from transcript analysis in the first release.
- No replacement of the existing meeting page; the board and AI review are additional surfaces.

## Approved Product Shape

The feature has three connected surfaces.

### Meeting Page

The existing meeting detail page remains the administrative and historical surface. It contains the meeting title, date, Zoom information, participants, schedule data, transcript, summary, tasks, and notes.

The page gains entry points for:

- opening the meeting board;
- checking whether a Zoom recording is available;
- manually starting audio transcription;
- reviewing and publishing AI outcome drafts.

### Meeting Board

The meeting board is a separate route or mode, for example `/meetings/{id}/board`.

It is designed for screen sharing during the Zoom call. The surface should be quieter and more focused than the full meeting detail page. It should not show administrative tabs or heavy settings.

The board should include:

- meeting title, date, and compact participant context;
- a way back to the meeting detail page;
- a board composition panel for added people, departments, and pinned tasks;
- task sections for the live discussion;
- a lightweight materials area for links and short notes.

The board does not store task copies. It computes and displays a live task slice from the current portal task data.

### AI Outcomes Review

The AI workflow happens after the meeting. It is not part of the live board.

Moderators manually start transcription when it is worth spending money on that meeting. After transcription, AI prepares an editable draft containing:

- meeting summary;
- decisions;
- new task candidates.

Moderators can edit the draft and choose which tasks to create. Publishing the draft saves the final summary and decisions to the meeting and creates only the selected tasks.

## Meeting Board Behavior

### Default Board Scope

The board starts with tasks for the meeting participants.

Included tasks should be grouped by task status and urgency rather than shown as a generic Kanban board. The first release should prioritize scanability during a call.

Recommended sections:

- urgent tasks;
- in-progress tasks;
- tasks in review;
- completed this week.

Overdue tasks should stay inside their relevant work section and use a distinct visual signal. The first release should not add a separate overdue section unless a later design explicitly expands the board.

### Hybrid Context Additions

Moderators can add more context to a board:

- individual team members;
- departments;
- pinned individual tasks.

Adding a department expands the board context to include visible tasks for members in that department, subject to existing role and department visibility rules.

Pinned tasks should appear even if they do not match the participant or department scope, as long as the current viewer has permission to see the task.

### Time Window

The completed section should default to tasks completed in the last seven days. The exact label should use user-facing wording such as `Done this week`.

The first release does not need configurable date ranges. A later release can add presets if meeting formats require it.

### Board Materials

The board supports lightweight meeting materials:

- links to documents, videos, or other resources;
- short manual notes;
- optional labels or descriptions for links.

These materials belong to the board/meeting, not to a task, unless a moderator explicitly creates a task from them later.

### Task Actions

The board should allow quick task actions that are already safe under the current permission model:

- open the task detail page;
- change task status when the current user has permission;
- create a new task;
- add a short task update/comment if supported by existing task update permissions.

Detailed editing remains on the task detail page.

## AI Transcription and Outcomes

### Manual Processing Policy

The first release uses manual transcription only.

The portal should not auto-transcribe every meeting. This avoids unnecessary AI spend for quick or low-importance calls.

The meeting page should show statuses such as:

- AI processing off or not started;
- Zoom recording not ready;
- Zoom recording ready;
- transcribing;
- transcript ready;
- outcome draft ready;
- published;
- failed.

### Audio Handling

The portal must not persist Zoom audio files.

Processing flow:

1. A moderator clicks `Transcribe audio`.
2. Backend requests Zoom cloud recording files for the meeting.
3. Backend selects an audio recording file.
4. Backend downloads the audio to a temporary stream or temporary file.
5. Backend sends the temporary audio to OpenAI transcription.
6. Backend saves the transcript text and processing metadata.
7. Backend deletes the temporary audio file in a `finally` path for success and failure cases.

The portal may continue storing the Zoom recording URL that already exists in the meeting model. Long-term audio storage remains Zoom's responsibility.

### Transcription Model

Default model: `gpt-4o-mini-transcribe`.

Rationale:

- better first-release balance of quality and cost than legacy `whisper-1`;
- official OpenAI pricing lists approximately `$0.003` per audio minute, or about `$0.18` for a one-hour meeting;
- `gpt-4o-transcribe` can remain a future higher-quality manual option at approximately `$0.006` per audio minute, or about `$0.36` for a one-hour meeting.

The design intentionally does not use `gpt-4o-transcribe-diarize` in the first release. Diarization can label speakers as `Speaker 1`, `Speaker 2`, and so on, but the portal would still need a review UI to map speaker labels to real participants. That added complexity is better handled later.

References:

- OpenAI pricing: `https://developers.openai.com/api/docs/pricing`
- OpenAI speech-to-text guide: `https://developers.openai.com/api/docs/guides/speech-to-text`
- `gpt-4o-mini-transcribe`: `https://developers.openai.com/api/docs/models/gpt-4o-mini-transcribe`
- `gpt-4o-transcribe`: `https://developers.openai.com/api/docs/models/gpt-4o-transcribe`
- `gpt-4o-transcribe-diarize`: `https://developers.openai.com/api/docs/models/gpt-4o-transcribe-diarize`

### AI Outcome Draft

After transcription, AI produces only:

- a concise meeting summary;
- a list of decisions;
- new task candidates.

Task candidates should include fields only when confidently inferred:

- title;
- description;
- assignee candidate;
- deadline candidate;
- urgency;
- source meeting id.

The system should clearly mark AI output as a draft. No task is created until a moderator confirms it.

### Moderator Review

The review UI should let the moderator:

- edit the summary;
- edit, add, or remove decisions;
- edit task candidate fields;
- select which task candidates to create;
- publish outcomes.

Publishing should:

- save the final summary to the meeting;
- save the final decisions to the meeting;
- create selected tasks;
- link created tasks to the meeting;
- keep unselected candidates only inside the current draft record and never create tasks from them.

## Data Model Direction

The implementation should avoid overloading the existing `notes` field for structured board and AI data.

### Meeting Board Data

The first release should use a dedicated one-to-one board settings record per meeting, for example `meeting_board_settings`.

That record should store:

- meeting id;
- added member ids;
- added department ids;
- pinned task ids;
- materials, including URL, title, optional description, and ordering;
- board notes;
- timestamps and author metadata.

The implementation can use JSONB or PostgreSQL arrays inside that dedicated record for the first release. The important product boundary is that board settings are structured data, separate from free-text meeting notes.

### AI Processing Data

The first release should keep one current AI processing state per meeting, for example `meeting_ai_processing`.

The portal does not need a historical archive of audio transcription attempts in the first release. A rerun can replace the current draft and latest processing metadata after explicit moderator confirmation.

The current processing record should store:

- meeting id;
- status;
- transcript source, including `openai_audio`;
- transcription model;
- started_at;
- completed_at;
- error message;
- transcript character count;
- optional audio duration and estimated cost;
- draft summary;
- draft decisions;
- draft task candidates;
- published_at and published_by_id when published.

The existing meeting fields can keep holding final `transcript`, `parsed_summary`, and `decisions` where appropriate, but draft and processing metadata should not be hidden inside free-text notes.

## Permissions

Meeting board visibility should follow existing meeting and task visibility rules.

Recommended first-release rules:

- meeting participants can view the meeting board if they can view the meeting;
- moderators and admins can manage board composition and materials;
- moderators and admins can start AI transcription;
- moderators and admins can review and publish AI outcomes;
- task quick actions still use existing task permission checks;
- tasks created from AI drafts are created by the moderator who confirms publication.

The board must not bypass task visibility. Adding a department or pinned task only makes visible tasks appear for users who already have permission to view them.

## Existing System Fit

The repository already has:

- a meetings module with detail tabs for transcript, summary, tasks, and notes;
- Zoom cloud recording status checks;
- a Zoom transcript path that downloads `TRANSCRIPT` files and saves `transcript_source='zoom_api'`;
- a voice transcription service using OpenAI `whisper-1`;
- AI meeting summary parsing that can create task previews.

This design should extend those capabilities instead of replacing them all at once.

Expected changes later:

- add a Zoom audio download method alongside the existing transcript download method;
- make the OpenAI transcription model configurable;
- preserve Zoom transcript fetch as fallback or legacy behavior;
- adjust the current summary parsing flow so it supports the new manual draft review rather than automatic creation.

## MVP Phases

### MVP 1: Meeting Board

- Add board entry point from meeting detail.
- Add a separate board route.
- Auto-seed board scope from participants.
- Add member, department, and pinned-task context controls.
- Render urgent, in-progress, review, and done-this-week sections.
- Add lightweight links/materials and board notes.
- Support safe task opening and basic task actions.

### MVP 2: Manual AI Transcription

- Show Zoom recording readiness.
- Add `Transcribe audio` action.
- Download Zoom audio temporarily.
- Transcribe with `gpt-4o-mini-transcribe`.
- Save transcript text and processing metadata.
- Delete temporary audio.

### MVP 3: AI Outcome Draft Review

- Generate summary, decisions, and new task candidates.
- Add moderator review UI.
- Publish final outcomes.
- Create only selected tasks.

## Later Enhancements

- Speaker diarization and speaker-to-participant mapping.
- Automatic transcription for explicitly important recurring meeting schedules.
- A richer live `Start meeting` mode.
- AI-assisted updates to existing tasks.
- Meeting protocol export.
- Per-schedule processing policies.
- Cost reporting by meeting or period.

## Validation Direction

Backend validation should cover:

- board scope computation respects task visibility;
- added departments and pinned tasks do not bypass permissions;
- Zoom audio temporary file cleanup happens on success and failure;
- transcript source and processing status transitions;
- AI draft publication creates only selected tasks;
- unconfirmed drafts do not mutate tasks or final meeting decisions.

Frontend validation should cover:

- meeting board sections render expected task groups;
- board context controls are moderator-only;
- regular participants cannot start transcription or publish AI outcomes;
- transcription statuses are understandable;
- AI outcome review requires explicit confirmation.

Manual QA should cover:

- opening the board from a meeting and sharing it at desktop widths;
- adding a participant, department, pinned task, link, and note;
- running a manual transcription on a meeting with a Zoom recording;
- confirming no audio file remains in portal storage after processing;
- editing and publishing an AI outcome draft;
- verifying that rejected task candidates are not created.

## Approved Decisions

- The feature is `Preparation + Meeting Board + Outcomes`, not a full live workspace.
- The meeting board is a separate shareable surface from the meeting detail page.
- The board uses hybrid task context: participants by default, plus manually added people, departments, and pinned tasks.
- AI transcription is manual-only in the first release.
- The portal does not persist Zoom audio files.
- The default transcription model is `gpt-4o-mini-transcribe`.
- Speaker diarization is out of scope for the first release.
- AI produces only summary, decisions, and new task candidates.
- Moderators must confirm drafts before final data is saved or tasks are created.
