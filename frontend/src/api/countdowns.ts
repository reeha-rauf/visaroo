import { api } from "./client";

/** A persistent, user-pinned deadline countdown (stored server-side). */
export interface Countdown {
  id: string;
  title: string;
  /** ISO 8601 date (YYYY-MM-DD). The client derives "days remaining" from this. */
  targetDate: string;
  /** The DeadlineId it was pinned from, or null for a custom countdown. */
  sourceDeadlineId: string | null;
  note: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CountdownCreate {
  title: string;
  targetDate: string;
  sourceDeadlineId?: string | null;
  note?: string | null;
}

export async function getCountdowns(): Promise<Countdown[]> {
  const { data } = await api.get<Countdown[]>("/countdowns");
  return data;
}

export async function createCountdown(body: CountdownCreate): Promise<Countdown> {
  const { data } = await api.post<Countdown>("/countdowns", body);
  return data;
}

export async function updateCountdown(
  id: string,
  body: CountdownCreate,
): Promise<Countdown> {
  const { data } = await api.put<Countdown>(`/countdowns/${id}`, body);
  return data;
}

export async function deleteCountdown(id: string): Promise<void> {
  await api.delete(`/countdowns/${id}`);
}

/**
 * Lightweight cross-component signal: fired whenever countdowns change (create/delete)
 * anywhere in the app, so the global countdown dock can refresh without prop-drilling.
 */
const COUNTDOWNS_CHANGED = "visaroo:countdowns-changed";

export function emitCountdownsChanged(): void {
  window.dispatchEvent(new Event(COUNTDOWNS_CHANGED));
}

export function onCountdownsChanged(handler: () => void): () => void {
  window.addEventListener(COUNTDOWNS_CHANGED, handler);
  return () => window.removeEventListener(COUNTDOWNS_CHANGED, handler);
}
