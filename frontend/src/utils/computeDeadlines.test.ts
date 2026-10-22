import { describe, expect, it } from "vitest";
import { emptyProfile, type Profile } from "../api/profile";
import { computeDeadlines } from "./computeDeadlines";

function stemProfile(over: Partial<Profile> = {}): Profile {
  return {
    ...emptyProfile(),
    visaType: "STEM_OPT",
    statusPhase: "active",
    programEndDate: "2025-05-15",
    eadEndDate: "2027-05-01",
    i20ExpiryDate: "2025-05-15",
    visaStampExpiry: "2028-01-01",
    passportExpiry: "2030-01-01",
    ...over,
  };
}

describe("computeDeadlines — applicability", () => {
  it("STEM OPT profile yields its applicable deadlines", () => {
    const today = new Date(2027, 0, 1); // 2027-01-01
    const result = computeDeadlines(stemProfile(), today);
    const ids = result.map((d) => d.id);
    expect(ids).toContain("ead_expiry");
    expect(ids).toContain("stem_window_open");
    expect(ids).toContain("stem_deadline");
    expect(ids).toContain("grace_period_end");
    expect(ids).toContain("visa_stamp_expiry");
    // H-1B-only deadlines must NOT appear
    expect(ids).not.toContain("i94_expiry");
    expect(ids).not.toContain("h1b_petition_expiry");
  });

  it("H-1B profile yields H-1B deadlines and not F-1/OPT ones", () => {
    const today = new Date(2027, 0, 1);
    const p: Profile = {
      ...emptyProfile(),
      visaType: "H-1B",
      statusPhase: "approved",
      i94ExpiryDate: "2027-09-30",
      h1bPetitionExpiry: "2027-09-30",
    };
    const ids = computeDeadlines(p, today).map((d) => d.id);
    expect(ids).toContain("i94_expiry");
    expect(ids).toContain("h1b_petition_expiry");
    expect(ids).not.toContain("opt_deadline");
    expect(ids).not.toContain("stem_window_open");
  });
});

describe("computeDeadlines — missing data", () => {
  it("missing eadEndDate → STEM deadlines are na with null date", () => {
    const today = new Date(2027, 0, 1);
    const result = computeDeadlines(stemProfile({ eadEndDate: null }), today);
    const stemWindow = result.find((d) => d.id === "stem_window_open")!;
    expect(stemWindow.date).toBeNull();
    expect(stemWindow.tier).toBe("na");
    expect(stemWindow.daysRemaining).toBeNull();
  });
});

describe("computeDeadlines — sort order", () => {
  it("orders critical before warning before upcoming before ok", () => {
    const today = new Date(2027, 0, 1);
    // Construct dates that fall into distinct tiers.
    const p = stemProfile({
      eadEndDate: "2027-01-05", // stem_deadline ~ -60 => expired, window ~ -90 expired; ead_expiry in 4 days => critical
      visaStampExpiry: "2027-02-01", // ~31 days => upcoming
      passportExpiry: "2030-01-01", // far => ok
    });
    const result = computeDeadlines(p, today);
    const tiers = result.map((d) => d.tier);
    // The array must be non-decreasing in tier rank.
    const rank: Record<string, number> = {
      critical: 0, warning: 1, upcoming: 2, ok: 3, expired: 4, na: 5,
    };
    for (let i = 1; i < tiers.length; i++) {
      expect(rank[tiers[i]]).toBeGreaterThanOrEqual(rank[tiers[i - 1]]);
    }
  });
});

describe("computeDeadlines — overrides (REQ-7)", () => {
  it("an override date replaces the computed value and flags isOverridden", () => {
    const today = new Date(2027, 0, 1);
    const p = stemProfile({ deadlineOverrides: { grace_period_end: "2027-12-25" } });
    const grace = computeDeadlines(p, today).find((d) => d.id === "grace_period_end")!;
    expect(grace.isOverridden).toBe(true);
    expect(grace.date?.toISOString().slice(0, 10)).toBe("2027-12-25");
  });
});
