/**
 * Parse a date string as a local date.
 *
 * JS `new Date("2026-02-14")` treats date-only strings as UTC midnight,
 * which shifts to the previous day in UTC- timezones (e.g. America/Denver
 * shows Feb 13 instead of Feb 14).
 *
 * Adding `T00:00:00` (without `Z`) forces local interpretation.
 * Full ISO datetime strings (with time/timezone) pass through unchanged.
 */
export function parseLocalDate(dateStr: string | null | undefined): Date {
  if (typeof dateStr !== "string") return new Date(NaN);
  const normalized = dateStr.trim();
  if (!normalized) return new Date(NaN);

  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    return new Date(normalized + "T00:00:00");
  }
  return new Date(normalized);
}

/**
 * Format a date-only API value without introducing timezone shifts.
 *
 * For plain `YYYY-MM-DD` values, format by string parts instead of `Date`
 * so the rendered day stays stable in every browser timezone.
 */
export function formatDateOnly(
  dateStr: string | null | undefined,
  options: { includeYear?: boolean } = {}
): string {
  if (typeof dateStr !== "string") return "";
  const normalized = dateStr.trim();
  if (!normalized) return "";

  const match = normalized.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (match) {
    const [, year, month, day] = match;
    return options.includeYear ? `${day}.${month}.${year}` : `${day}.${month}`;
  }

  const parsed = parseLocalDate(normalized);
  if (Number.isNaN(parsed.getTime())) return "";

  return parsed.toLocaleDateString("ru-RU", options.includeYear
    ? { day: "2-digit", month: "2-digit", year: "numeric" }
    : { day: "2-digit", month: "2-digit" });
}

/**
 * Convert a local Date into `YYYY-MM-DD` without UTC normalization.
 */
export function toLocalDateString(date: Date): string {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return "";

  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

/**
 * Parse a datetime string from the API as UTC.
 *
 * The backend stores datetimes as naive UTC. Ideally the API sends them
 * with "+00:00" suffix, but for safety: if the string has no timezone
 * indicator (no Z, no +/-offset), append "Z" so JavaScript interprets
 * it as UTC instead of the browser's local timezone.
 */
export function parseUTCDate(dateStr: string | null | undefined): Date {
  if (typeof dateStr !== "string") return new Date(NaN);
  const normalized = dateStr.trim();
  if (!normalized) return new Date(NaN);

  // Already has timezone info (Z or +/-offset) — parse as-is
  if (/Z|[+-]\d{2}:\d{2}$/.test(normalized)) {
    return new Date(normalized);
  }
  // No timezone info — treat as UTC
  return new Date(normalized + "Z");
}
