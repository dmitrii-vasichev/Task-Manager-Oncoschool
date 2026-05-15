# Content Factory Sprint 34 Variant Coverage Design

## Goal

Show publication editors whether saved channel adaptations are complete and current before they copy or schedule content.

## Background

Sprint 31 introduced deterministic channel adaptations for Telegram, VK, email, push, Max, and Dzen. Sprint 32 made those adaptations durable through saved publication variants and tracked `source_version_number`.

The current detail page shows the selected channel state, but it does not summarize the whole adaptation set. Editors still need to click through each channel to understand what is missing or stale after the source publication text changes.

## Scope

- Add a frontend-only coverage helper for saved publication variants.
- Add a compact readiness summary inside the existing `Адаптации` panel.
- Keep existing save/copy/reset behavior unchanged.
- Add source guards and helper tests.

## Out of Scope

- Backend schema or API changes.
- AI generation.
- Platform publishing integrations.
- Variant approval workflow.
- Automatic regeneration of saved variants.

## UX

The `Адаптации` panel should show a compact `Готовность адаптаций` block above channel tabs:

- saved channel count, such as `2 из 6 каналов сохранено`;
- ready channel count, excluding stale variants;
- missing channel labels;
- stale channel labels when a saved variant was based on an older publication version;
- a plain Russian next action.

Expected next actions:

- no saved variants: `Сохраните первую адаптацию`;
- stale variants exist: `Обновите адаптации после изменения публикации`;
- missing variants exist: `Заполните недостающие каналы`;
- all variants saved and current: `Адаптации готовы`.

## Data Rules

- Expected channels are Telegram, VK, email, push, Max, and Dzen.
- A channel is saved only when a saved variant exists and `body_text` is not blank.
- A saved variant is stale when `source_version_number` is lower than the publication `version_number`.
- Ready variants are saved variants that are not stale.

## Validation

- Focused helper and source guard tests pass.
- Full frontend test suite, typecheck, lint, build, and whitespace checks pass.
