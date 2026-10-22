import { useState } from "react";
import {
  diffInCalendarDays,
  parseISO,
  projectedCapDate,
} from "../utils/deadlineCalculations";
import { WarningIcon } from "./icons";

interface Props {
  daysUsed: number;
  cap: number;
  eadStartDate?: string | null;
  onUpdate: (days: number) => Promise<void> | void;
}

/** Tier based on days remaining against the cap (REQ-3). */
function tierFor(remaining: number): "ok" | "warning" | "critical" {
  if (remaining <= 7) return "critical";
  if (remaining <= 30) return "warning";
  return "ok";
}

export default function UnemploymentCounter({
  daysUsed,
  cap,
  eadStartDate,
  onUpdate,
}: Props) {
  const [value, setValue] = useState<string>(String(daysUsed ?? 0));
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const used = Math.min(Math.max(daysUsed ?? 0, 0), cap);
  const remaining = Math.max(cap - used, 0);
  const percent = cap ? Math.min(100, (used / cap) * 100) : 0;
  const tier = tierFor(remaining);
  const projected = projectedCapDate(eadStartDate, used, cap, new Date());

  async function commit() {
    const n = Number(value);
    if (!Number.isInteger(n) || n < 0 || n > cap) {
      setError(`Enter a whole number between 0 and ${cap}.`);
      return;
    }
    setError(null);
    setSaving(true);
    try {
      await onUpdate(n);
      setSaved(true);
      setTimeout(() => setSaved(false), 1600);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card hover">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>Unemployment days</h3>
        <span className={`tier-pill ${tier}`}>
          {remaining} of {cap} remaining
        </span>
      </div>

      <div className="counter-bar" style={{ marginTop: 14 }}>
        <div className={`counter-fill ${tier}`} style={{ width: `${percent}%` }} />
      </div>

      <div className="row" style={{ gap: 12, marginTop: 12, flexWrap: "wrap" }}>
        <div style={{ maxWidth: 180 }}>
          <label>Days used</label>
          <input
            type="number"
            min={0}
            max={cap}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onBlur={commit}
            style={{ margin: 0 }}
          />
        </div>
        {saving && <span className="muted">Saving…</span>}
        {saved && <span className="muted">✓ Saved</span>}
      </div>
      {error && <div className="warn" style={{ marginTop: 10 }}>{error}</div>}

      {projected && used > 0 && (
        <p className="muted" style={{ marginTop: 10, marginBottom: 0 }}>
          At your current rate, you'd reach the {cap}-day cap around{" "}
          <strong>{projected.toISOString().slice(0, 10)}</strong>. (Estimate.)
        </p>
      )}
      {tier !== "ok" && (
        <p className={tier === "critical" ? "warn" : "muted"} style={{ marginTop: 10, marginBottom: 0 }}>
          {tier === "critical" ? (
            <>
              <WarningIcon size={14} /> You're within 7 days of the unemployment cap.
              Losing status is a real risk — talk to your DSO.
            </>
          ) : (
            "Heads up: you're within 30 days of the unemployment cap."
          )}
        </p>
      )}
    </div>
  );
}
