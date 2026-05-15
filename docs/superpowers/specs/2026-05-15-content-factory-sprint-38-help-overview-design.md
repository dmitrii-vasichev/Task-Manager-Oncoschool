# Content Factory Sprint 38 Help Overview Design

## Goal

Expand the Content Factory help page from a short orientation note into a detailed onboarding overview that explains the operating model, why the module exists, which manual workflows it replaces, what is already supported, and what will be automated later.

## User Problem

The Content Factory now has many sections and operational concepts. A non-developer user can open the workspace, see campaigns, publications, audiences, metrics, retrospectives, references, guests, and review queues, and reasonably feel that the system is too large or unclear.

The help page should reduce that intimidation. It should explain the module as a practical workflow, not as a list of database entities.

## Scope

Sprint 38 covers the global overview help only:

- Rich introduction: what Content Factory is and what problem it solves.
- Research basis: the module follows best-practice patterns from campaign workspaces, editorial approval flows, custom/manual channels, taxonomy-first planning, metric snapshots, and retrospectives.
- Operating model: campaign -> publications -> channel adaptations -> review -> publish evidence -> metrics -> retrospective learning.
- Current state: what users can already do manually or semi-automatically.
- Future state: what is intentionally planned later, including Excel import, cross-channel planning matrix, publishing queue, platform integrations, and automated metrics.
- First-use guidance: how a user can start without needing every field or integration on day one.

Out of scope:

- Detailed per-section help for calendar, publications, campaigns, audiences, metrics, retrospectives, references, and guests. Those are reserved for Sprint 39 through Sprint 41.
- Backend schema or API changes.
- New routing.
- Automatic publishing or metric integrations.

## UX Direction

Keep the page inside the existing Content Factory help route: `/content-factory/help`.

The page should feel like an internal operations manual that is readable in one sitting:

- Clear Russian headings and body copy.
- No system-code labels or unexplained field names.
- Full-width sections and compact cards rather than nested card-heavy decoration.
- Icons may support section scanning, but text should carry the meaning.
- The layout should work on mobile and desktop without horizontal overflow or cramped text.

Recommended page sections:

1. Hero/onboarding summary: what this workspace is and why it exists.
2. "Why it is built this way": short explanation of the deep-research and market-practice basis.
3. Operating model: the lifecycle from campaign idea to retrospective learning.
4. Current capabilities: manual and semi-automated features available now.
5. Planned automation: what will come later and why it is not hidden as current functionality.
6. First safe path: a simple step-by-step way to start using Content Factory today.
7. Section directory: existing links to all Content Factory sections remain available.
8. Glossary: keep and enrich the existing terminology.

## Testing

Use source-guard tests for this sprint because the change is a static help page and existing tests already guard Content Factory UI structure.

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

