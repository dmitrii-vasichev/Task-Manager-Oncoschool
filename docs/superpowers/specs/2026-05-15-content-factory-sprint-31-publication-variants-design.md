# Content Factory Sprint 31 Publication Variants Design

## Context

Content Factory now supports the practical manual publishing ledger: publication records, workflow actions, publication history, publish package, publication fact capture, metric import, and metric insights.

The recovered research warns against treating one body text as the final text for every channel. A Telegram post, VK post, email, push notification, Max post, and Dzen outline have different constraints and review needs. The right next step is to create a manual adaptation surface before AI draft generation or backend variant persistence.

## Goal

Add a frontend-only publication adaptation panel on the publication detail page.

The panel should help a user create copy-ready variants from the current publication text:

- Telegram post;
- VK post;
- email announcement;
- push notification;
- Max short post;
- Dzen outline.

## Scope

- Frontend-only implementation.
- Pure helper in `frontend/src/lib/contentFactoryUtils.ts`.
- New component under `frontend/src/components/content-factory`.
- Publication detail wiring below the publish package and above media/history sections.
- Helper tests and source guards.
- Durable plan/status/test docs.

## Non-Goals

- No backend schema, migration, endpoint, or `cf_publication_variant` table.
- No saving edited variants.
- No AI generation.
- No style-guide model.
- No platform posting API.
- No medical factcheck automation.

## UX

The new panel title is `Адаптации`.

It appears near the publication text and publish package, because it is part of preparing the publication for manual posting.

The panel shows:

- a small channel selector with readable Russian labels;
- the selected variant title/subject;
- the selected variant body;
- a copy button: `Скопировать адаптацию`;
- compact metadata: channel label, intended use, and length hint;
- warnings when source text is missing.

The UI should stay practical and quiet, matching the existing operational Content Factory surfaces. It should not look like a marketing landing page or an AI generation console.

## Variant Rules

The helper is deterministic and does not invent facts.

- Telegram: keeps the source title and body, adds a concise CTA placeholder.
- VK: keeps the title and body, adds a line for discussion/comment.
- Email: returns subject, preheader, and body.
- Push: creates a short title and short body from the publication title/body.
- Max: creates a short social version with the source title and compressed body.
- Dzen: returns a title and simple outline based on the source body.

If the source body is missing, variants should say `Текст публикации не заполнен` and expose a warning.

If UTM exists, copy text should include a compact `UTM:` block so the user can paste the tracking data next to the adapted copy.

## Data Design

Add `buildContentFactoryPublicationVariants(input)`.

Input:

- `publication`: id, title, body text, UTM;
- optional `platform`, `format`, and `bundle` references for context labels.

Output:

- `sourceTitle`;
- `sourceBody`;
- `contextRows`;
- `variants`.

Each variant includes:

- `key`;
- `channelLabel`;
- `useCase`;
- `title`;
- `body`;
- `lengthHint`;
- `warnings`;
- `copyText`.

## Testing

Automated tests:

- helper creates the expected six variant keys and readable channel labels;
- helper includes source body, UTM, and channel-specific text in copy output;
- helper handles missing source body with readable warnings;
- source guard confirms publication detail renders `ContentFactoryPublicationVariants`, the component uses `buildContentFactoryPublicationVariants`, and the copy button uses `navigator.clipboard.writeText`.

Manual QA:

- open a publication detail page with body text and UTM;
- confirm `Адаптации` appears below the publish package;
- switch between channels and confirm the preview updates;
- copy an adaptation and paste it into a scratch note;
- open a publication without body text and confirm warning copy is readable.

