# Dashboard Task Card Height Synchronization Design

## Summary

The dashboard task block already renders overdue and active tasks as internal groups. The next refinement should synchronize task card heights across the two desktop task columns so the block reads as a tidy set of horizontal rows instead of two uneven vertical stacks.

The synchronization applies only inside the dashboard task block. The adjacent `Activity in 7 days` card remains independent and should not be height-matched to task cards or to the task block.

## Goals

- Make the desktop task block feel visually calmer when overdue and active task titles have different lengths.
- Keep the existing distinction between `Overdue` and `Active` tasks.
- Avoid giving every card a fixed global height.
- Preserve natural card height on mobile and narrow tablet layouts.
- Avoid placeholder task cards or empty visible cells when one group has more tasks than the other.

## Non-Goals

- No change to task sorting, grouping, status semantics, visibility, or department scope behavior.
- No change to the `Activity in 7 days` card layout.
- No change to the task board card component.
- No truncation policy change beyond what the current compact dashboard task card already uses.
- No global fixed height for all dashboard task cards.

## Approved Approach

On desktop, when both `Overdue` and `Active` groups have content, the task block should render the visible task previews as paired visual rows:

- row 1: `overdue[0]` beside `active[0]`
- row 2: `overdue[1]` beside `active[1]`
- row 3: `overdue[2]` beside `active[2]`

Each row should stretch both task cells to the height of the taller task card in that row. The card content itself remains content-driven; only the row equalizes the visual height. This avoids the overly airy result of assigning one fixed height to every card.

If one group has more visible tasks than the other, the remaining cards continue in their own column. The layout may use empty grid cells internally to preserve column alignment, but those cells must not render as visible placeholders and must not be exposed as fake tasks.

## Responsive Behavior

Desktop:

- Use row-level synchronization only when the task block is wide enough for two readable internal columns.
- Keep visible group headings above the synchronized grid.
- Stretch paired task cards to the same row height.

Tablet:

- Use synchronized rows only at the same breakpoint where the current two-column task group layout is readable.
- Fall back to stacked groups when the block is too narrow.

Mobile:

- Keep the existing stacked order: `Overdue` first, then `Active`.
- Do not synchronize heights.
- Do not introduce horizontal scrolling.

No-overdue state:

- Continue hiding the `Overdue` group.
- Let active tasks use the available width as they do today.
- Do not render hidden empty cells for a missing overdue group.

## Accessibility

- Group headings must remain visible text.
- Expand buttons must remain real buttons with `aria-expanded` and `aria-controls`.
- Hidden alignment cells, if used, must be non-interactive and `aria-hidden`.
- Keyboard and screen-reader navigation must not expose duplicate task links.
- Mobile reading order must remain overdue tasks before active tasks.

## Acceptance Criteria

- With overdue and active tasks on desktop, paired task cards in the same visual row have matching heights.
- Task cards are not assigned one fixed global height.
- Extra tasks in the longer group continue in the correct column without visible placeholder cards.
- With zero overdue tasks, the overdue group remains hidden and no empty synchronization cells are visible.
- On mobile, groups remain stacked with natural card heights.
- The `Activity in 7 days` card is not height-synchronized with the task block.
- Existing independent expansion behavior for `Overdue` and `Active` still works.
