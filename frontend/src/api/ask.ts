import { api } from "./client";

export interface Citation {
  n: number;
  title: string;
  source: string;
  url: string | null;
  excerpt: string;
}

export interface AskResponse {
  answer: string;
  statusLabel: string; // PROPOSED | FINAL | IN_EFFECT | UNCLEAR
  citations: Citation[];
  grounded: boolean;
  personalized: boolean;
  disclaimer: string;
}

export interface AskTurn {
  question: string;
  answer: string;
}

export async function askImpact(
  question: string,
  history: AskTurn[] = [],
): Promise<AskResponse> {
  const { data } = await api.post<AskResponse>("/ask", { question, history });
  return data;
}

// Status label → display text + chip tone (reuses the creator-feed status-chip CSS).
export const STATUS_DISPLAY: Record<string, { text: string; tone: string }> = {
  PROPOSED: { text: "Proposed — not yet in effect", tone: "amber" },
  FINAL: { text: "Final rule", tone: "blue" },
  IN_EFFECT: { text: "Currently in effect", tone: "green" },
  UNCLEAR: { text: "Status unclear", tone: "grey" },
};
