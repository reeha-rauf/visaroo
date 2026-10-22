/** Deadline proximity badge logic (design.md "Deadline display"). */
export type BadgeTone = "red" | "amber" | "grey" | "normal";

export interface DateBadge {
  tone: BadgeTone;
  label: string;
  daysAway: number | null;
}

export function dateBadge(iso?: string | null): DateBadge {
  if (!iso) return { tone: "normal", label: "—", daysAway: null };
  const target = new Date(iso + "T00:00:00");
  if (isNaN(target.getTime())) return { tone: "normal", label: iso, daysAway: null };

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((target.getTime() - today.getTime()) / 86_400_000);

  if (days < 0) return { tone: "grey", label: "Expired", daysAway: days };
  if (days <= 7) return { tone: "red", label: `in ${days} day${days === 1 ? "" : "s"}`, daysAway: days };
  if (days <= 30) return { tone: "amber", label: `in ${days} days`, daysAway: days };
  return { tone: "normal", label: `in ${days} days`, daysAway: days };
}
