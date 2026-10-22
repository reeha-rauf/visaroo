/**
 * Attorney Help — case brief generator (spec REQ-2 / TASK-3).
 *
 * Pure, client-side, no server calls, no LLM. Builds a structured brief from the user's
 * profile + computed deadlines, and renders it to plain text for copy/download/mailto.
 */
import type { Profile } from "../api/profile";
import {
  STEM_OPT_UNEMPLOYMENT_CAP,
  OPT_UNEMPLOYMENT_CAP,
  type UrgencyTier,
} from "./deadlineCalculations";
import type { ComputedDeadline } from "./computeDeadlines";
import { generateSuggestedQuestions } from "./suggestedQuestions";

export const BRIEF_DISCLAIMER =
  "Visaroo does not provide legal advice and is not a law firm. This brief is for " +
  "informational purposes only. Always verify information with your DSO or a qualified " +
  "immigration attorney.";

export interface BriefInput {
  profile: Profile;
  computedDeadlines: ComputedDeadline[];
  situationDescription: string;
}

export interface BriefDate {
  label: string;
  date: string;
}

export interface BriefDeadline {
  label: string;
  date: string;
  daysRemaining: number;
  tier: UrgencyTier;
}

export interface CaseBrief {
  generatedAt: string;
  visaType: string;
  statusPhase: string;
  keyDates: BriefDate[];
  activeDeadlines: BriefDeadline[];
  unemploymentStatus?: string;
  stemOptExtensionStatus?: string;
  h1bPetitionStatus?: string;
  upcomingTravel?: string;
  situationDescription: string;
  suggestedQuestions: string[];
  disclaimer: string;
}

function formatDate(d: Date | string | null): string {
  if (!d) return "—";
  const date = typeof d === "string" ? new Date(d + "T00:00:00") : d;
  if (isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function buildKeyDates(p: Profile): BriefDate[] {
  const out: BriefDate[] = [];
  if (p.programEndDate) out.push({ label: "Program end", date: formatDate(p.programEndDate) });
  if (p.eadEndDate) out.push({ label: "EAD expiry", date: formatDate(p.eadEndDate) });
  if (p.i94ExpiryDate) out.push({ label: "I-94 expiry", date: formatDate(p.i94ExpiryDate) });
  if (p.gracePeriodEndDate)
    out.push({ label: "Grace period end", date: formatDate(p.gracePeriodEndDate) });
  if (p.visaStampExpiry)
    out.push({ label: "Visa stamp expiry", date: formatDate(p.visaStampExpiry) });
  return out;
}

function buildUnemploymentStatus(p: Profile): string | undefined {
  if (p.visaType !== "OPT" && p.visaType !== "STEM_OPT") return undefined;
  if (p.unemploymentDaysUsed == null) return undefined;
  const cap = p.visaType === "STEM_OPT" ? STEM_OPT_UNEMPLOYMENT_CAP : OPT_UNEMPLOYMENT_CAP;
  return `${p.unemploymentDaysUsed} of ${cap} days used`;
}

function buildTravelSummary(p: Profile): string | undefined {
  if (!p.upcomingTravel || p.upcomingTravel.length === 0) return undefined;
  return p.upcomingTravel
    .map((t) => `${t.destination} (departs ${t.departureDate}${t.returnDate ? `, returns ${t.returnDate}` : ""})`)
    .join("; ");
}

export function generateBrief(input: BriefInput): CaseBrief {
  const { profile, computedDeadlines, situationDescription } = input;

  const activeDeadlines: BriefDeadline[] = computedDeadlines
    .filter((d) => d.daysRemaining !== null && d.daysRemaining >= 0 && d.daysRemaining <= 60)
    .map((d) => ({
      label: d.label,
      date: formatDate(d.date),
      daysRemaining: d.daysRemaining as number,
      tier: d.tier,
    }));

  return {
    generatedAt: new Date().toISOString(),
    visaType: profile.visaType,
    statusPhase: profile.statusPhase,
    keyDates: buildKeyDates(profile),
    activeDeadlines,
    unemploymentStatus: buildUnemploymentStatus(profile),
    stemOptExtensionStatus: profile.stemOptStatus ?? undefined,
    h1bPetitionStatus: profile.petitionStatus ?? undefined,
    upcomingTravel: buildTravelSummary(profile),
    situationDescription,
    suggestedQuestions: generateSuggestedQuestions(profile, computedDeadlines),
    disclaimer: BRIEF_DISCLAIMER,
  };
}

export function briefToPlainText(brief: CaseBrief): string {
  const lines: string[] = [];
  const rule = "────────────────────────────────";
  lines.push("VISAROO IMMIGRATION CASE BRIEF");
  lines.push(`Generated: ${new Date(brief.generatedAt).toLocaleString()}`);
  lines.push(rule, "");

  lines.push("VISA STATUS");
  lines.push(`Type: ${brief.visaType}`);
  lines.push(`Phase: ${brief.statusPhase}`, "");

  if (brief.keyDates.length) {
    lines.push("KEY DATES");
    brief.keyDates.forEach((d) => lines.push(`${d.label} — ${d.date}`));
    lines.push("");
  }

  if (brief.activeDeadlines.length) {
    lines.push("UPCOMING DEADLINES (next 60 days)");
    brief.activeDeadlines.forEach((d) =>
      lines.push(`${d.label} — ${d.date} (${d.daysRemaining} days)`),
    );
    lines.push("");
  }

  if (brief.unemploymentStatus) {
    lines.push("UNEMPLOYMENT DAYS", brief.unemploymentStatus, "");
  }
  if (brief.stemOptExtensionStatus) {
    lines.push("STEM OPT EXTENSION STATUS", brief.stemOptExtensionStatus, "");
  }
  if (brief.h1bPetitionStatus) {
    lines.push("H-1B PETITION STATUS", brief.h1bPetitionStatus, "");
  }
  if (brief.upcomingTravel) {
    lines.push("UPCOMING TRAVEL", brief.upcomingTravel, "");
  }
  if (brief.situationDescription.trim()) {
    lines.push("MY SITUATION", brief.situationDescription.trim(), "");
  }

  lines.push("SUGGESTED QUESTIONS FOR MY ATTORNEY / DSO");
  brief.suggestedQuestions.forEach((q, i) => lines.push(`${i + 1}. ${q}`));
  lines.push("");

  lines.push(rule, "DISCLAIMER", brief.disclaimer);
  return lines.join("\n");
}
