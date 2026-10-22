import { api } from "./client";

export const FEED_VISA_TAGS = [
  "ALL",
  "F-1",
  "OPT",
  "STEM_OPT",
  "H-1B",
  "H-4",
  "J-1",
] as const;

export type PostStatusLabel = "rumor_reported" | "proposed" | "final" | "in_effect";
export type MatchStatus = "pending" | "matched" | "no_match";

// Display text + chip tone per status label (REQ-3).
export const STATUS_LABELS: Record<PostStatusLabel, { text: string; tone: string }> = {
  rumor_reported: { text: "Reported — not confirmed", tone: "grey" },
  proposed: { text: "Proposed — not yet final", tone: "amber" },
  final: { text: "Final rule", tone: "blue" },
  in_effect: { text: "In effect", tone: "green" },
};

// Status filter chips (value -> label). "" = All.
export const STATUS_FILTERS: { value: string; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "proposed", label: "Proposed" },
  { value: "final", label: "Final" },
  { value: "in_effect", label: "In effect" },
  { value: "rumor_reported", label: "Reported" },
];

export interface CreatorPost {
  id: string;
  creatorId: number;
  creatorDisplayName: string;
  headline: string;
  body: string;
  visaTypeTags: string[];
  statusLabel: PostStatusLabel;
  sourceUrl: string;
  sourceLabel: string;
  effectiveDate: string | null;
  expiryDate: string | null;
  postedAt: string;
  updatedAt: string;
  matchStatus: MatchStatus;
  matchedDocumentTitle: string | null;
  matchedDocumentUrl: string | null;
}

export interface CreatorPostCreate {
  headline: string;
  body: string;
  visaTypeTags: string[];
  statusLabel: PostStatusLabel;
  sourceUrl: string;
  sourceLabel: string;
  effectiveDate?: string | null;
  expiryDate?: string | null;
}

export async function getCreatorPosts(
  visaType?: string,
  statusLabel?: string,
): Promise<CreatorPost[]> {
  const params: Record<string, string> = {};
  if (visaType && visaType !== "ALL") params.visaType = visaType;
  if (statusLabel) params.statusLabel = statusLabel;
  const { data } = await api.get<CreatorPost[]>("/creator-posts", { params });
  return data;
}

export async function getCreatorPost(id: string): Promise<CreatorPost> {
  const { data } = await api.get<CreatorPost>(`/creator-posts/${id}`);
  return data;
}

export async function createCreatorPost(body: CreatorPostCreate): Promise<CreatorPost> {
  const { data } = await api.post<CreatorPost>("/creator-posts", body);
  return data;
}

export async function deleteCreatorPost(id: string): Promise<void> {
  await api.delete(`/creator-posts/${id}`);
}

/** Rough "x ago" formatter for post timestamps. */
export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diff / 60000);
  if (mins < 60) return `${Math.max(mins, 1)}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}
