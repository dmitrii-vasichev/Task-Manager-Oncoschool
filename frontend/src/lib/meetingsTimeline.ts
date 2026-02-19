import { parseUTCDate } from "@/lib/dateUtils";
import { PROJECT_TIMEZONE } from "@/lib/meetingDateTime";
import { getDayLabel, getDayShort } from "@/lib/meetingDayTheme";
import type { DayOfWeek } from "@/lib/meetingDayTheme";
import type { Meeting, MeetingSchedule } from "@/lib/types";

const MOSCOW_DAY_PARTS_FORMATTER = new Intl.DateTimeFormat("en-CA", {
  timeZone: PROJECT_TIMEZONE,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

const MOSCOW_TIME_FORMATTER = new Intl.DateTimeFormat("ru-RU", {
  timeZone: PROJECT_TIMEZONE,
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

type DayParts = {
  year: number;
  month: number;
  day: number;
};

export type TimelineMeetingSource = "schedule" | "manual" | "schedule_missing";

export interface TimelineMeetingItem {
  id: string;
  meeting: Meeting;
  meetingAt: Date;
  meetingTimestamp: number;
  meetingTimeLabel: string;
  dayKey: string;
  dayOfWeek: DayOfWeek;
  source: TimelineMeetingSource;
  scheduleId: string | null;
  schedule: MeetingSchedule | null;
  isPast: boolean;
}

export interface TimelineDayGroup {
  dayKey: string;
  dayOfWeek: DayOfWeek;
  dayLabel: string;
  dayShort: string;
  isToday: boolean;
  items: TimelineMeetingItem[];
}

export interface BuildMeetingsTimelineParams {
  upcomingMeetings: Meeting[];
  pastMeetings: Meeting[];
  schedules: MeetingSchedule[];
  now?: Date;
}

function toDayPartsInMoscow(date: Date): DayParts {
  const values: Partial<DayParts> = {};

  for (const part of MOSCOW_DAY_PARTS_FORMATTER.formatToParts(date)) {
    if (part.type === "year" || part.type === "month" || part.type === "day") {
      values[part.type] = Number(part.value);
    }
  }

  return {
    year: values.year ?? 1970,
    month: values.month ?? 1,
    day: values.day ?? 1,
  };
}

function toMoscowDayKey(date: Date): string {
  const { year, month, day } = toDayPartsInMoscow(date);
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function getDayOfWeekFromDayKey(dayKey: string): DayOfWeek {
  const [year, month, day] = dayKey.split("-").map(Number);
  const utcDay = new Date(Date.UTC(year, month - 1, day)).getUTCDay();
  return (utcDay === 0 ? 7 : utcDay) as DayOfWeek;
}

function compareDayKeys(a: string, b: string, nowDayKey: string): number {
  const aPast = a < nowDayKey;
  const bPast = b < nowDayKey;

  if (aPast !== bPast) {
    return aPast ? 1 : -1;
  }

  if (aPast) {
    return b.localeCompare(a);
  }

  return a.localeCompare(b);
}

export function buildMeetingsTimeline({
  upcomingMeetings,
  pastMeetings,
  schedules,
  now = new Date(),
}: BuildMeetingsTimelineParams): TimelineDayGroup[] {
  const nowDayKey = toMoscowDayKey(now);
  const nowTimestamp = now.getTime();
  const scheduleById = new Map<string, MeetingSchedule>(
    schedules.map((schedule) => [schedule.id, schedule]),
  );

  const dayGroups = new Map<string, TimelineMeetingItem[]>();
  const seenMeetingIds = new Set<string>();

  for (const meeting of [...upcomingMeetings, ...pastMeetings]) {
    if (seenMeetingIds.has(meeting.id)) {
      continue;
    }
    seenMeetingIds.add(meeting.id);

    if (!meeting.meeting_date) {
      continue;
    }

    const meetingAt = parseUTCDate(meeting.meeting_date);
    const meetingTimestamp = meetingAt.getTime();

    if (Number.isNaN(meetingTimestamp)) {
      continue;
    }

    const dayKey = toMoscowDayKey(meetingAt);
    const dayOfWeek = getDayOfWeekFromDayKey(dayKey);

    const schedule = meeting.schedule_id
      ? (scheduleById.get(meeting.schedule_id) ?? null)
      : null;

    const source: TimelineMeetingSource = !meeting.schedule_id
      ? "manual"
      : schedule
        ? "schedule"
        : "schedule_missing";

    const item: TimelineMeetingItem = {
      id: meeting.id,
      meeting,
      meetingAt,
      meetingTimestamp,
      meetingTimeLabel: MOSCOW_TIME_FORMATTER.format(meetingAt),
      dayKey,
      dayOfWeek,
      source,
      scheduleId: meeting.schedule_id,
      schedule,
      isPast: meetingTimestamp < nowTimestamp,
    };

    const items = dayGroups.get(dayKey);
    if (items) {
      items.push(item);
    } else {
      dayGroups.set(dayKey, [item]);
    }
  }

  const sortedDayKeys = Array.from(dayGroups.keys()).sort((a, b) =>
    compareDayKeys(a, b, nowDayKey),
  );

  return sortedDayKeys.map((dayKey) => {
    const items = dayGroups.get(dayKey) ?? [];
    items.sort((a, b) => a.meetingTimestamp - b.meetingTimestamp);

    const dayOfWeek = getDayOfWeekFromDayKey(dayKey);

    return {
      dayKey,
      dayOfWeek,
      dayLabel: getDayLabel(dayOfWeek),
      dayShort: getDayShort(dayOfWeek),
      isToday: dayKey === nowDayKey,
      items,
    };
  });
}
