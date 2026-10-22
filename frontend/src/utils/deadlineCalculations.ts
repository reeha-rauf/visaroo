/**
 * Deadline Tracker — pure calculation functions (spec: .kiro/specs/deadline-tracker).
 *
 * Per steering (deadline-tracker.md): these are the ONLY place deadline dates are
 * computed. No LLM, no API. Every function returns `Date | null` and yields null when a
 * required source date is missing. All date math is done in UTC-safe calendar terms.
 */

export type UrgencyTier =
  | "critical"
  | "warning"
  | "upcoming"
  | "ok"
  | "expired"
  | "na";

export const OPT_UNEMPLOYMENT_CAP = 90;
export const STEM_OPT_UNEMPLOYMENT_CAP = 150;

/** Parse an ISO (YYYY-MM-DD) string into a Date at local midnight, or null. */
export function parseISO(value?: string | null): Date | null {
  if (!value) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!m) return null;
  const [, y, mo, d] = m;
  const date = new Date(Number(y), Number(mo) - 1, Number(d));
  // Guard against rollovers like 2027-02-30 becoming March.
  if (
    date.getFullYear() !== Number(y) ||
    date.getMonth() !== Number(mo) - 1 ||
    date.getDate() !== Number(d)
  ) {
    return null;
  }
  date.setHours(0, 0, 0, 0);
  return date;
}

/** Add (or subtract) whole calendar days, returning a new Date. */
export function addDays(date: Date, days: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  d.setHours(0, 0, 0, 0);
  return d;
}

/** Whole calendar days between two dates (b - a), ignoring time-of-day. */
export function diffInCalendarDays(a: Date, b: Date): number {
  const x = new Date(a.getFullYear(), a.getMonth(), a.getDate());
  const y = new Date(b.getFullYear(), b.getMonth(), b.getDate());
  return Math.round((y.getTime() - x.getTime()) / 86_400_000);
}

/** Shift an ISO source date by `days`; null if the source is missing/invalid. */
function shift(iso: string | null | undefined, days: number): Date | null {
  const d = parseISO(iso);
  return d ? addDays(d, days) : null;
}

// ----------------------------- Formulas -----------------------------
// Each takes the relevant ISO source date(s) and returns Date | null.

export const optWindowOpen = (programEndDate?: string | null) =>
  shift(programEndDate, -90);

export const optDeadline = (programEndDate?: string | null) =>
  shift(programEndDate, -60);

export const stemOptWindowOpen = (eadEndDate?: string | null) =>
  shift(eadEndDate, -90);

export const stemOptDeadline = (eadEndDate?: string | null) =>
  shift(eadEndDate, -60);

/** Grace period for F-1 / OPT: 60 days after program end. */
export const gracePeriodEnd = (programEndDate?: string | null) =>
  shift(programEndDate, 60);

/** Grace period for STEM OPT: 60 days after EAD end. */
export const stemGracePeriodEnd = (eadEndDate?: string | null) =>
  shift(eadEndDate, 60);

/** Grace period for H-1B: 60 days after I-94 expiry. */
export const h1bGracePeriodEnd = (i94ExpiryDate?: string | null) =>
  shift(i94ExpiryDate, 60);

/** SEVP reporting deadline: 10 days after a reportable event. */
export const sevpDeadline = (lastReportableEventDate?: string | null) =>
  shift(lastReportableEventDate, 10);

/** Plain passthrough for user-entered expiry-style dates (EAD, I-20, etc.). */
export const asDate = (iso?: string | null) => parseISO(iso);

/**
 * Projected cap-hit date based on current burn rate:
 *   projected = eadStart + (cap / (daysUsed / daysSinceEadStart)) days
 * Returns null unless daysUsed > 0 and daysSinceEadStart > 0.
 */
export function projectedCapDate(
  eadStartDate: string | null | undefined,
  daysUsed: number,
  cap: number,
  today: Date,
): Date | null {
  const start = parseISO(eadStartDate);
  if (!start || daysUsed <= 0) return null;
  const daysSinceStart = diffInCalendarDays(start, today);
  if (daysSinceStart <= 0) return null;
  const rate = daysUsed / daysSinceStart; // unemployment days accrued per calendar day
  if (rate <= 0) return null;
  const daysToCap = Math.round(cap / rate);
  return addDays(start, daysToCap);
}

/** Urgency tier from a date relative to today (REQ-2). */
export function getUrgencyTier(date: Date | null, today: Date): UrgencyTier {
  if (!date) return "na";
  const days = diffInCalendarDays(today, date);
  if (days < 0) return "expired";
  if (days <= 7) return "critical";
  if (days <= 30) return "warning";
  if (days <= 90) return "upcoming";
  return "ok";
}

/** Days remaining until a date (negative if past), or null. */
export function daysRemaining(date: Date | null, today: Date): number | null {
  if (!date) return null;
  return diffInCalendarDays(today, date);
}

export function unemploymentCapFor(visaType: string): number {
  return visaType === "STEM_OPT" ? STEM_OPT_UNEMPLOYMENT_CAP : OPT_UNEMPLOYMENT_CAP;
}
