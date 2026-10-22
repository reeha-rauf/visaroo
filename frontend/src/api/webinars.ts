import { api } from "./client";

// Visa-type filter chips (includes ALL). Underscore form matches the backend.
export const WEBINAR_VISA_TAGS = [
  "ALL",
  "F-1",
  "OPT",
  "STEM_OPT",
  "H-1B",
  "H-4",
  "J-1",
] as const;

export type HostType = "official" | "verified_creator" | "community";

export interface Webinar {
  id: string;
  title: string;
  hostName: string;
  hostType: HostType;
  postedBy: number | null;
  startDateUtc: string;
  durationMinutes: number | null;
  visaTypeTags: string[];
  description: string;
  registrationUrl: string;
  speakerBio: string | null;
  relatedResources: string[] | null;
  createdAt: string;
  updatedAt: string;
}

export async function getWebinars(
  visaType?: string,
  includePast = false,
): Promise<Webinar[]> {
  const params: Record<string, string | boolean> = {};
  if (visaType && visaType !== "ALL") params.visaType = visaType;
  if (includePast) params.includePast = true;
  const { data } = await api.get<Webinar[]>("/webinars", { params });
  return data;
}

/** Format a UTC ISO datetime in the browser's local timezone with the UTC offset. */
export function formatLocal(iso: string): string {
  const d = new Date(iso);
  const date = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(d);
  return date;
}
