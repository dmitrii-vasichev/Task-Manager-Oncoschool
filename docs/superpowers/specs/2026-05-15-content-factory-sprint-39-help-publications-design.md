# Content Factory Sprint 39 Help For Calendar, Publications, Adaptations, And Readiness Design

## Goal

Add detailed practical help for the most important day-to-day publication workflow: calendar planning, publication records, channel adaptations, and the readiness checklist.

Sprint 38 explained the whole Content Factory concept. Sprint 39 should answer the next user question: "How do I use this to plan and prepare a real post?"

## User Problem

The current module can already plan publications, edit publication details, save channel adaptations, copy publish packages, record publish facts, and show readiness. Without detailed help, a user may still not understand:

- why the calendar is more than a date list;
- what belongs in a publication record;
- why one source text needs channel-specific adaptations;
- how saved, missing, and stale adaptations should be interpreted;
- what the readiness checklist means before and after publication;
- what can be done manually today before automatic publishing exists.

## Scope

This sprint expands the existing `/content-factory/help` page with practical guidance for:

- Calendar planning.
- Publication records.
- Channel adaptations.
- Readiness checklist.
- Manual publishing handoff.
- After-publication evidence and metrics.

The help should use Russian, user-facing wording and avoid system field names unless the term is visible in the UI.

Out of scope:

- New backend APIs.
- New routes.
- Inline contextual help widgets on individual pages.
- Detailed help for campaigns, review queue, audiences, metrics, effectiveness, retrospectives, references, and guest stories. Those remain for Sprint 40 and Sprint 41.
- Automatic publishing or automatic metric collection.

## UX Direction

Keep the content in `/content-factory/help` so users have one reliable help entry point. Add a practical section after the first-use path and before the section directory.

Recommended structure:

1. "Планирование публикации: от календаря до готовности" intro.
2. Four workflow cards:
   - Calendar: planned date, filters, grouped dates, overdue and unscheduled items.
   - Publication record: title/body, platform, format, rubric, nosology, responsible user, UTM, audience targets, publish evidence.
   - Adaptations: one source idea, channel-specific saved variants, ready/missing/stale meanings, copy handoff.
   - Readiness checklist: before-publish checks, after-publish checks, why some items wait for publication.
3. A compact "manual workflow today" sequence:
   - create or import later,
   - schedule,
   - prepare text,
   - save adaptations,
   - review,
   - copy and publish manually,
   - record post URL,
   - add metrics.
4. A "common confusion" list:
   - scheduled date does not publish automatically yet;
   - adaptation saved from an older source version can become stale;
   - metrics are evidence, not decorative reporting;
   - readiness is a decision aid, not a blocker for every draft.

## Testing

Use the existing Content Factory source guard suite. Add one new test that verifies the help page contains the Sprint 39 practical guidance headings and key phrases.

Focused verification:

```bash
cd frontend && node --test --experimental-strip-types src/components/content-factory/contentFactorySourceGuards.test.ts
```

Full frontend verification:

```bash
cd frontend && npm test
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd frontend && npm run build
git diff --check
```

