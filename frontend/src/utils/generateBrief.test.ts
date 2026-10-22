import { describe, expect, it } from "vitest";
import { emptyProfile, type Profile } from "../api/profile";
import type { ComputedDeadline } from "./computeDeadlines";
import { briefToPlainText, generateBrief } from "./generateBrief";

function dl(label: string, days: number, tier: ComputedDeadline["tier"]): ComputedDeadline {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return {
    id: "stem_deadline",
    label,
    date,
    isOverridden: false,
    tier,
    daysRemaining: days,
    description: "",
    consequence: "",
    regulationCite: "",
    officialUrl: "",
  };
}

const stem: Profile = {
  ...emptyProfile(),
  visaType: "STEM_OPT",
  statusPhase: "active",
  eadEndDate: "2027-05-01",
  unemploymentDaysUsed: 40,
  stemOptStatus: "pending",
};

describe("generateBrief", () => {
  it("includes deadlines within 60 days and excludes far ones", () => {
    const deadlines = [dl("Soon", 10, "warning"), dl("Later", 120, "ok")];
    const brief = generateBrief({ profile: stem, computedDeadlines: deadlines, situationDescription: "" });
    const labels = brief.activeDeadlines.map((d) => d.label);
    expect(labels).toContain("Soon");
    expect(labels).not.toContain("Later");
  });

  it("includes unemployment status for STEM OPT", () => {
    const brief = generateBrief({ profile: stem, computedDeadlines: [], situationDescription: "" });
    expect(brief.unemploymentStatus).toBe("40 of 150 days used");
  });

  it("always carries a disclaimer and suggested questions", () => {
    const brief = generateBrief({ profile: stem, computedDeadlines: [], situationDescription: "" });
    expect(brief.disclaimer).toBeTruthy();
    expect(brief.suggestedQuestions.length).toBeGreaterThan(0);
  });

  it("plain text contains key sections", () => {
    const brief = generateBrief({
      profile: stem,
      computedDeadlines: [dl("STEM filing deadline", 20, "warning")],
      situationDescription: "I switched employers last month.",
    });
    const text = briefToPlainText(brief);
    expect(text).toContain("VISAROO IMMIGRATION CASE BRIEF");
    expect(text).toContain("UNEMPLOYMENT DAYS");
    expect(text).toContain("STEM filing deadline");
    expect(text).toContain("MY SITUATION");
    expect(text).toContain("DISCLAIMER");
  });

  it("key dates are formatted dates, not counts", () => {
    const brief = generateBrief({ profile: stem, computedDeadlines: [], situationDescription: "" });
    const ead = brief.keyDates.find((d) => d.label === "EAD expiry");
    expect(ead?.date).toMatch(/\w+ \d{1,2}, \d{4}/); // e.g. "May 1, 2027"
  });
});
