/**
 * Deadline Tracker — assemble the sorted, tier-tagged deadline list (spec TASK-3).
 *
 * Pure function: given a profile and `today`, produce every applicable deadline with
 * its tier and days-remaining. Applies manual overrides (REQ-7) and the design's sort
 * order. No LLM, no API.
 */
import type { Profile } from "../api/profile";
import {
  DEADLINE_DEFINITIONS,
  type DeadlineDefinition,
  type DeadlineId,
} from "../data/deadlineDefinitions";
import {
  daysRemaining,
  getUrgencyTier,
  parseISO,
  type UrgencyTier,
} from "./deadlineCalculations";

export interface ComputedDeadline {
  id: DeadlineId;
  label: string;
  date: Date | null;
  isOverridden: boolean;
  tier: UrgencyTier;
  daysRemaining: number | null;
  description: string;
  consequence: string;
  regulationCite: string;
  officialUrl: string;
}

const TIER_ORDER: Record<UrgencyTier, number> = {
  critical: 0,
  warning: 1,
  upcoming: 2,
  ok: 3,
  expired: 4,
  na: 5,
};

function isApplicable(def: DeadlineDefinition, profile: Profile): boolean {
  if (!def.applicableVisaTypes.includes(profile.visaType)) return false;
  if (def.applicablePhases && !def.applicablePhases.includes(profile.statusPhase)) {
    return false;
  }
  return true;
}

/**
 * Resolve a deadline's date: a per-deadline override in `deadlineOverrides` wins over
 * the computed value. Returns both the date and whether an override was applied.
 */
function resolveDate(
  def: DeadlineDefinition,
  profile: Profile,
): { date: Date | null; isOverridden: boolean } {
  const override = profile.deadlineOverrides?.[def.id];
  if (override) {
    const d = parseISO(override);
    if (d) return { date: d, isOverridden: true };
  }
  return { date: def.calculate(profile), isOverridden: false };
}

export function computeDeadlines(
  profile: Profile,
  today: Date,
): ComputedDeadline[] {
  const applicable = DEADLINE_DEFINITIONS.filter((def) => isApplicable(def, profile));

  const computed: ComputedDeadline[] = applicable.map((def) => {
    const { date, isOverridden } = resolveDate(def, profile);
    return {
      id: def.id,
      label: def.label,
      date,
      isOverridden,
      tier: getUrgencyTier(date, today),
      daysRemaining: daysRemaining(date, today),
      description: def.description,
      consequence: def.consequence,
      regulationCite: def.regulationCite,
      officialUrl: def.officialUrl,
    };
  });

  // Sort: by tier bucket, then within a bucket by soonest first — except Expired,
  // which shows most-recent (closest to today) first (design.md sort order).
  computed.sort((a, b) => {
    const tierDiff = TIER_ORDER[a.tier] - TIER_ORDER[b.tier];
    if (tierDiff !== 0) return tierDiff;

    // na items have no date; keep stable.
    if (a.date === null && b.date === null) return 0;
    if (a.date === null) return 1;
    if (b.date === null) return -1;

    const aTime = a.date.getTime();
    const bTime = b.date.getTime();
    if (a.tier === "expired") return bTime - aTime; // most recent past first
    return aTime - bTime; // soonest upcoming first
  });

  return computed;
}
