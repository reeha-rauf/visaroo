import { api } from "./client";

// ---- Domain constants (mirror backend app/profile_domain.py) ----
export const VISA_TYPES = [
  "F-1",
  "OPT",
  "STEM_OPT",
  "H-1B",
  "H-4",
  "J-1",
  "Other",
] as const;

export const STATUS_PHASES: Record<string, string[]> = {
  "F-1": [
    "coursework",
    "pre-completion OPT",
    "post-completion OPT",
    "STEM OPT extension",
    "grace period",
  ],
  OPT: ["active", "grace period"],
  STEM_OPT: ["active", "grace period"],
  "H-1B": ["pending", "approved", "cap-exempt", "transfer in progress"],
  "H-4": ["active", "grace period"],
  "J-1": ["active", "grace period"],
  Other: ["active", "grace period"],
};

export const STEM_OPT_STATUSES = ["not_started", "applied", "pending", "approved"];
export const PETITION_STATUSES = ["pending", "approved", "cap_exempt"];
export const LEAD_TIME_OPTIONS = [90, 60, 30, 14, 7];

// ---- Types (mirror backend ProfileOut / ProfileUpsert) ----
export interface TravelEntry {
  destination: string;
  departureDate: string;
  returnDate?: string | null;
}

export interface NotificationPreferences {
  emailEnabled: boolean;
  alerts: {
    deadlineApproaching: boolean;
    newRuleAffectingStatus: boolean;
    newCreatorPost: boolean;
    newWebinar: boolean;
  };
  deadlineLeadTimeDays: number[];
}

export interface PersonalizationToggles {
  visaStatus: boolean;
  keyDates: boolean;
  travel: boolean;
  employer: boolean;
}

export interface ComputedDates {
  optApplicationWindowOpens?: string | null;
  optApplicationDeadline?: string | null;
  stemFilingWindowStart?: string | null;
  stemFilingWindowEnd?: string | null;
  gracePeriodEnd?: string | null;
  unemploymentDaysRemaining?: number | null;
  unemploymentCap?: number | null;
}

export interface Profile {
  fullName: string;
  countryOfOrigin?: string | null;
  universityOrEmployer?: string | null;
  fieldOrTitle?: string | null;

  visaType: string;
  statusPhase: string;

  programStartDate?: string | null;
  programEndDate?: string | null;
  i20ExpiryDate?: string | null;
  portOfEntryDate?: string | null;
  visaStampExpiry?: string | null;
  eadStartDate?: string | null;
  eadEndDate?: string | null;
  nextSevpReportingDate?: string | null;
  nextRenewalReminder?: string | null;
  gracePeriodEndDate?: string | null;

  employerName?: string | null;
  employerEVerify?: string | null;
  stemOptStatus?: string | null;
  i983OnFile?: boolean | null;
  unemploymentDaysUsed?: number | null;

  petitionReceiptNumber?: string | null;
  petitionStatus?: string | null;
  i94ExpiryDate?: string | null;
  employerEIN?: string | null;
  h1bTransferInProgress?: boolean | null;
  h1bPetitionExpiry?: string | null;
  capGapEnd?: string | null;

  passportExpiry?: string | null;
  lastReportableEventDate?: string | null;
  lastSevpReportedDate?: string | null;
  deadlineOverrides?: Record<string, string> | null;

  lastUsEntryDate?: string | null;
  upcomingTravel?: TravelEntry[] | null;
  recentCountriesVisited?: string[] | null;
  advanceParoleFiled?: boolean | null;

  dsoName?: string | null;
  dsoEmail?: string | null;
  attorneyName?: string | null;
  attorneyEmail?: string | null;

  notifications: NotificationPreferences;
  aiPersonalizationFields: PersonalizationToggles;
}

export interface ProfileOut extends Profile {
  email: string;
  computed: ComputedDates;
  createdAt: string;
  updatedAt: string;
}

export function emptyProfile(): Profile {
  return {
    fullName: "",
    visaType: "OPT",
    statusPhase: "active",
    notifications: {
      emailEnabled: true,
      alerts: {
        deadlineApproaching: true,
        newRuleAffectingStatus: true,
        newCreatorPost: false,
        newWebinar: false,
      },
      deadlineLeadTimeDays: [90, 30, 7],
    },
    aiPersonalizationFields: {
      visaStatus: true,
      keyDates: true,
      travel: false,
      employer: false,
    },
  };
}

// ---- API calls ----
export async function getProfile(): Promise<ProfileOut | null> {
  try {
    const { data } = await api.get<ProfileOut>("/profile");
    return data;
  } catch (e: any) {
    if (e?.response?.status === 404) return null;
    throw e;
  }
}

export async function putProfile(profile: Profile): Promise<ProfileOut> {
  const { data } = await api.put<ProfileOut>("/profile", profile);
  return data;
}

export async function deleteProfile(): Promise<void> {
  await api.delete("/profile");
}

/** Strip nulls/empties so the backend's extra="forbid" + validators stay happy. */
export function cleanProfile(p: Profile): Profile {
  const out: any = { ...p };
  for (const k of Object.keys(out)) {
    if (out[k] === "" || out[k] === null) delete out[k];
  }
  // Required fields always present
  out.fullName = p.fullName || "";
  out.visaType = p.visaType;
  out.statusPhase = p.statusPhase;
  out.notifications = p.notifications;
  out.aiPersonalizationFields = p.aiPersonalizationFields;
  return out as Profile;
}
