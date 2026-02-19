import { DAY_OF_WEEK_LABELS, DAY_OF_WEEK_SHORT } from "@/lib/types";

export type DayOfWeek = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export interface MeetingDayTheme {
  dayOfWeek: DayOfWeek;
  badgeClassName: string;
}

const DEFAULT_DAY_OF_WEEK: DayOfWeek = 1;

const DAY_THEME_MAP: Record<DayOfWeek, MeetingDayTheme> = {
  1: {
    dayOfWeek: 1,
    badgeClassName: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  },
  2: {
    dayOfWeek: 2,
    badgeClassName: "bg-violet-500/10 text-violet-600 border-violet-500/20",
  },
  3: {
    dayOfWeek: 3,
    badgeClassName: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  },
  4: {
    dayOfWeek: 4,
    badgeClassName: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  },
  5: {
    dayOfWeek: 5,
    badgeClassName: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  },
  6: {
    dayOfWeek: 6,
    badgeClassName: "bg-cyan-500/10 text-cyan-600 border-cyan-500/20",
  },
  7: {
    dayOfWeek: 7,
    badgeClassName: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  },
};

function normalizeDayOfWeek(dayOfWeek: number): DayOfWeek {
  if (Number.isInteger(dayOfWeek) && dayOfWeek >= 1 && dayOfWeek <= 7) {
    return dayOfWeek as DayOfWeek;
  }
  return DEFAULT_DAY_OF_WEEK;
}

export function getDayTheme(dayOfWeek: number): MeetingDayTheme {
  return DAY_THEME_MAP[normalizeDayOfWeek(dayOfWeek)];
}

export function getDayLabel(dayOfWeek: number): string {
  const normalized = normalizeDayOfWeek(dayOfWeek);
  return DAY_OF_WEEK_LABELS[normalized];
}

export function getDayShort(dayOfWeek: number): string {
  const normalized = normalizeDayOfWeek(dayOfWeek);
  return DAY_OF_WEEK_SHORT[normalized];
}
