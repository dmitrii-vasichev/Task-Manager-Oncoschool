# Design Brief: Reports Module + Portal Rebranding

## UI Framework
- Library: shadcn/ui (Radix primitives + Tailwind)
- CSS: Tailwind CSS + CSS variables (HSL)
- Charts: recharts
- Icons: Lucide React
- Animations: tailwindcss-animate + custom keyframes in globals.css

## Theme
- Mode: Both (Light + Dark, class-based toggle)
- Style: Clean professional with warm accents — not sterile, not playful

## Color Palette

### Brand
- Primary: `hsl(174, 62%, 26%)` — Deep Teal (buttons, links, active states)
- Primary (dark): `hsl(174, 52%, 42%)` — lighter teal for dark mode
- Accent: `hsl(16, 76%, 58%)` — Warm Coral (highlights, secondary actions)
- Accent (dark): `hsl(16, 68%, 54%)`

### Surface
- Background: `hsl(200, 20%, 98%)` / dark: `hsl(210, 22%, 7%)`
- Card: `hsl(0, 0%, 100%)` / dark: `hsl(210, 20%, 10%)`
- Muted: `hsl(200, 18%, 94%)` / dark: `hsl(210, 16%, 16%)`
- Border: `hsl(210, 16%, 90%)` / dark: `hsl(210, 16%, 18%)`

### Semantic (existing)
- Destructive/Error: `hsl(0, 72%, 51%)`
- Status colors: blue (new), teal (progress), amber (review), green (done), gray (cancelled)
- Priority colors: red (urgent), orange (high), yellow (medium), slate (low)

### Semantic (new for reports)
- Delta positive: `--delta-positive` — green, reuse `--status-done-fg` palette
- Delta negative: `--delta-negative` — red, reuse `--priority-urgent-fg` palette

### Charts
- Chart 1: `hsl(174, 62%, 26%)` — Teal (primary metric)
- Chart 2: `hsl(16, 76%, 58%)` — Coral
- Chart 3: `hsl(262, 52%, 55%)` — Purple
- Chart 4: `hsl(43, 82%, 58%)` — Gold
- Chart 5: `hsl(200, 65%, 48%)` — Blue

## Typography
- Headings: Manrope (Google Fonts, cyrillic + latin)
- Body: Commissioner (Google Fonts, cyrillic + latin)
- Mono: Geist Mono (local, variable font)
- Extra size: `2xs` = 0.6875rem for micro-labels

## Layout
- Navigation: Collapsible sidebar (260px expanded / 72px collapsed)
- Mobile: Sheet/Drawer sidebar (280px)
- Max content width: fluid (no max-width cap)
- Border radius: 0.625rem (10px) base, `md` = 8px, `sm` = 6px
- Spacing scale: 4px base (Tailwind default)

### Sidebar Sections (after rebranding)
1. **Dashboard** — standalone top item
2. **— divider —**
3. **Задачи, Встречи** — core workflow
4. **— section: Аналитика —**
5. Аналитика, Отчёты (new)
6. **— section: Контент —**
7. Telegram-анализ
8. **— section: Управление —**
9. Рассылки, Настройки

### Branding
- Logo icon: GraduationCap in teal circle
- Title: "Онкошкола" (primary)
- Subtitle: "Портал" (replaces "Task Manager")

## Component Standards

### Buttons
- Rounded (border-radius from theme)
- Primary: solid teal, white text
- Secondary: muted background
- Ghost: transparent, hover → muted
- Destructive: red solid

### Cards
- White/dark surface, 1px border, 10px radius
- Subtle shadow on hover (optional)
- Staggered fade-in-up animation on page load

### KPI Cards (new — reports dashboard)
- Large number (text-3xl font-bold)
- Delta badge: green up-arrow / red down-arrow with percentage
- Muted label below
- 5 cards in responsive grid (1 col mobile → 5 col desktop)

### Charts (reports dashboard)
- recharts AreaChart / BarChart
- Period selector: 7 / 14 / 30 days (segmented control or tabs)
- Grid: 2-column layout on desktop
- Tooltip with date + formatted values
- Use chart-1 through chart-5 palette

### Tables
- Striped rows (even:bg-muted/30)
- Sticky header
- Sortable columns where applicable
- Compact padding for data-dense views

### Forms
- Input with border, focus ring (teal)
- Labels above inputs
- Inline validation errors (destructive color)

## Animations
- Page load: staggered fade-in-up (60ms intervals)
- Cards: card-enter (scale 0.98 → 1, translateY 8px → 0)
- Badges: badge-appear (scale 0.9 → 1)
- Skeletons: shimmer gradient animation
- Dialogs: scale-in (0.95 → 1) + translateY
- Global transitions: 200ms cubic-bezier(0.4, 0, 0.2, 1) on color/bg/border/shadow

## Reference
- Existing app design — consistent extension, no visual breaking changes
- Frontend design guide: `docs/ai/frontend-design.md`
