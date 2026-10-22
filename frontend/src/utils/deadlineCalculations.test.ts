import { describe, expect, it } from "vitest";
import {
  addDays,
  daysRemaining,
  diffInCalendarDays,
  getUrgencyTier,
  gracePeriodEnd,
  h1bGracePeriodEnd,
  optDeadline,
  optWindowOpen,
  parseISO,
  projectedCapDate,
  sevpDeadline,
  stemOptDeadline,
  stemOptWindowOpen,
} from "./deadlineCalculations";

const iso = (d: Date | null) => (d ? d.toISOString().slice(0, 10) : null);

describe("deadline formulas — standard cases", () => {
  it("OPT window opens 90 days before program end", () => {
    expect(iso(optWindowOpen("2026-05-15"))).toBe("2026-02-14");
  });
  it("OPT deadline is 60 days before program end", () => {
    expect(iso(optDeadline("2026-05-15"))).toBe("2026-03-16");
  });
  it("STEM filing window opens 90 days before EAD end", () => {
    expect(iso(stemOptWindowOpen("2027-05-01"))).toBe("2027-01-31");
  });
  it("STEM filing deadline is 60 days before EAD end", () => {
    expect(iso(stemOptDeadline("2027-05-01"))).toBe("2027-03-02");
  });
  it("F-1/OPT grace period is 60 days after program end", () => {
    expect(iso(gracePeriodEnd("2026-05-15"))).toBe("2026-07-14");
  });
  it("H-1B grace period is 60 days after I-94 expiry", () => {
    expect(iso(h1bGracePeriodEnd("2027-09-30"))).toBe("2027-11-29");
  });
  it("SEVP deadline is 10 days after a reportable event", () => {
    expect(iso(sevpDeadline("2026-03-01"))).toBe("2026-03-11");
  });
});

describe("missing source dates return null", () => {
  it("returns null when the source date is absent", () => {
    expect(optWindowOpen(null)).toBeNull();
    expect(optDeadline(undefined)).toBeNull();
    expect(stemOptWindowOpen("")).toBeNull();
  });
  it("returns null for an invalid calendar date", () => {
    expect(parseISO("2027-02-30")).toBeNull();
    expect(parseISO("not-a-date")).toBeNull();
  });
});

describe("urgency tiers", () => {
  const today = new Date(2026, 0, 1); // 2026-01-01

  it("na when date is null", () => {
    expect(getUrgencyTier(null, today)).toBe("na");
  });
  it("expired when date is in the past", () => {
    expect(getUrgencyTier(addDays(today, -1), today)).toBe("expired");
  });
  it("critical when the date is today (0 days)", () => {
    expect(getUrgencyTier(today, today)).toBe("critical");
  });
  it("critical within 7 days", () => {
    expect(getUrgencyTier(addDays(today, 7), today)).toBe("critical");
  });
  it("warning between 8 and 30 days", () => {
    expect(getUrgencyTier(addDays(today, 8), today)).toBe("warning");
    expect(getUrgencyTier(addDays(today, 30), today)).toBe("warning");
  });
  it("upcoming between 31 and 90 days", () => {
    expect(getUrgencyTier(addDays(today, 31), today)).toBe("upcoming");
    expect(getUrgencyTier(addDays(today, 90), today)).toBe("upcoming");
  });
  it("ok beyond 90 days", () => {
    expect(getUrgencyTier(addDays(today, 91), today)).toBe("ok");
  });
});

describe("leap year edge cases", () => {
  it("subtracting 90 days across a leap day (2028 is a leap year)", () => {
    // 2028-05-01 minus 90 days crosses Feb 29, 2028.
    expect(iso(optWindowOpen("2028-05-01"))).toBe("2028-02-01");
  });
  it("diffInCalendarDays counts the leap day", () => {
    // 2028-02-28 -> 2028-03-01 is 2 days because of Feb 29.
    const a = parseISO("2028-02-28")!;
    const b = parseISO("2028-03-01")!;
    expect(diffInCalendarDays(a, b)).toBe(2);
  });
});

describe("daysRemaining", () => {
  const today = new Date(2026, 0, 1);
  it("positive for future, negative for past, null for null", () => {
    expect(daysRemaining(addDays(today, 5), today)).toBe(5);
    expect(daysRemaining(addDays(today, -3), today)).toBe(-3);
    expect(daysRemaining(null, today)).toBeNull();
  });
});

describe("projectedCapDate", () => {
  it("projects a cap-hit date from the current burn rate", () => {
    // EAD started 100 days ago, 30 days used -> rate 0.3/day; cap 90 -> 300 days from start.
    const today = new Date(2026, 3, 11); // 2026-04-11
    const result = projectedCapDate("2026-01-01", 30, 90, today);
    expect(iso(result)).toBe(iso(addDays(parseISO("2026-01-01")!, 300)));
  });
  it("returns null when daysUsed is 0 or EAD start missing", () => {
    const today = new Date(2026, 3, 11);
    expect(projectedCapDate("2026-01-01", 0, 90, today)).toBeNull();
    expect(projectedCapDate(null, 30, 90, today)).toBeNull();
  });
});
