import { describe, expect, it } from "vitest";
import { emptyProfile, type Profile } from "../api/profile";
import type { ComputedDeadline } from "./computeDeadlines";
import { generateSuggestedQuestions } from "./suggestedQuestions";

const FALLBACK =
  "What are the most important things I should do to protect my status right now?";

function deadline(tier: ComputedDeadline["tier"]): ComputedDeadline {
  return {
    id: "opt_deadline",
    label: "OPT deadline",
    date: new Date(),
    isOverridden: false,
    tier,
    daysRemaining: 3,
    description: "",
    consequence: "",
    regulationCite: "",
    officialUrl: "",
  };
}

describe("generateSuggestedQuestions", () => {
  it("always includes the fallback question", () => {
    const qs = generateSuggestedQuestions(emptyProfile(), []);
    expect(qs).toContain(FALLBACK);
    expect(qs.length).toBeGreaterThanOrEqual(1);
  });

  it("OPT with >60 unemployment days includes the unemployment question", () => {
    const p: Profile = { ...emptyProfile(), visaType: "OPT", unemploymentDaysUsed: 70 };
    const qs = generateSuggestedQuestions(p, []);
    expect(qs.some((q) => q.includes("90 unemployment days"))).toBe(true);
  });

  it("STEM OPT pending includes the extension question", () => {
    const p: Profile = { ...emptyProfile(), visaType: "STEM_OPT", stemOptStatus: "pending" };
    const qs = generateSuggestedQuestions(p, []);
    expect(qs.some((q) => q.includes("STEM OPT extension is not approved"))).toBe(true);
  });

  it("no travel means no travel question", () => {
    const qs = generateSuggestedQuestions(emptyProfile(), []);
    expect(qs.some((q) => q.includes("re-enter the US"))).toBe(false);
  });

  it("critical deadline adds the urgent question", () => {
    const qs = generateSuggestedQuestions(emptyProfile(), [deadline("critical")]);
    expect(qs.some((q) => q.includes("within 7 days"))).toBe(true);
  });

  it("caps at 5 questions", () => {
    const p: Profile = {
      ...emptyProfile(),
      visaType: "OPT",
      unemploymentDaysUsed: 80,
      stemOptStatus: "pending",
      h1bTransferInProgress: true,
      upcomingTravel: [{ destination: "India", departureDate: "2027-01-01" }],
    };
    const qs = generateSuggestedQuestions(p, [deadline("critical")]);
    expect(qs.length).toBeLessThanOrEqual(5);
  });
});
