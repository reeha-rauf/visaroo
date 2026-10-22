import { useCallback, useEffect, useState } from "react";
import {
  deleteCountdown,
  getCountdowns,
  type Countdown,
} from "../api/countdowns";
import {
  daysRemaining,
  getUrgencyTier,
  parseISO,
} from "../utils/deadlineCalculations";
import { CloseIcon, PinIcon } from "./icons";

interface Props {
  /** Bump this to force a reload (e.g. after pinning a new countdown elsewhere). */
  refreshKey?: number;
  /** "strip" = compact horizontal pills (Feed); "full" = labelled block (Deadlines). */
  variant?: "strip" | "full";
  /** Heading shown above the countdowns in the "full" variant. */
  title?: string;
  /** Message shown when the user has no pinned countdowns (full variant only). */
  emptyHint?: string;
  onChange?: () => void;
}

function label(targetDate: string): string {
  const d = parseISO(targetDate);
  const days = daysRemaining(d, new Date());
  if (days === null) return "";
  if (days < 0) return `${Math.abs(days)}d ago`;
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  return `${days} days`;
}

/**
 * Persistent, always-visible countdown pills. Days-remaining and the urgency tier are
 * recomputed from the stored target date on every render (no stale values), matching
 * the deadline-tracker steering (client-side date math only).
 */
export default function PinnedCountdowns({
  refreshKey = 0,
  variant = "full",
  title = "Your countdowns",
  emptyHint,
  onChange,
}: Props) {
  const [items, setItems] = useState<Countdown[]>([]);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(() => {
    getCountdowns()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoaded(true));
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  async function remove(id: string) {
    setItems((prev) => prev.filter((c) => c.id !== id)); // optimistic
    try {
      await deleteCountdown(id);
    } finally {
      onChange?.();
    }
  }

  if (!loaded) return null;

  if (items.length === 0) {
    if (variant === "strip") return null;
    return (
      <div className="countdowns-block">
        <div className="countdowns-head"><PinIcon size={16} /> {title}</div>
        <p className="muted" style={{ margin: 0 }}>
          {emptyHint ?? "Pin a deadline below to keep a live countdown here."}
        </p>
      </div>
    );
  }

  const pills = items.map((c) => {
    const d = parseISO(c.targetDate);
    const tier = getUrgencyTier(d, new Date());
    return (
      <div className={`countdown-pill tier-border ${tier}`} key={c.id}>
        <span className={`tier-dot ${tier}`} />
        <div className="countdown-pill-text">
          <strong title={c.note ?? undefined}>{c.title}</strong>
          <span className="muted">
            {label(c.targetDate)} · {c.targetDate}
          </span>
        </div>
        <button
          className="countdown-remove"
          aria-label={`Remove countdown ${c.title}`}
          title="Remove"
          onClick={() => remove(c.id)}
        >
          <CloseIcon size={13} />
        </button>
      </div>
    );
  });

  if (variant === "strip") {
    return (
      <div className="countdowns-strip" aria-label="Pinned countdowns">
        <span className="countdowns-strip-label"><PinIcon size={14} /> Countdowns</span>
        <div className="countdowns-strip-pills">{pills}</div>
      </div>
    );
  }

  return (
    <div className="countdowns-block">
      <div className="countdowns-head"><PinIcon size={16} /> {title}</div>
      <div className="countdowns-grid">{pills}</div>
      <p className="muted countdowns-note">
        Countdowns are estimates to help you organize — not legal advice. Verify with
        your DSO or an immigration attorney.
      </p>
    </div>
  );
}
