import { useCallback, useEffect, useState } from "react";
import {
  deleteCountdown,
  emitCountdownsChanged,
  getCountdowns,
  onCountdownsChanged,
  type Countdown,
} from "../api/countdowns";
import { useAuth } from "../context/AuthContext";
import { getUrgencyTier, parseISO } from "../utils/deadlineCalculations";
import { ChevronLeftIcon, ClockIcon, CloseIcon } from "./icons";

interface Remaining {
  past: boolean;
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
}

/** Time left until local midnight of the target date, broken into d/h/m/s. */
function remaining(targetDate: string, now: number): Remaining {
  const d = parseISO(targetDate);
  if (!d) return { past: false, days: 0, hours: 0, minutes: 0, seconds: 0 };
  let ms = d.getTime() - now;
  const past = ms < 0;
  ms = Math.abs(ms);
  const days = Math.floor(ms / 86_400_000);
  const hours = Math.floor((ms % 86_400_000) / 3_600_000);
  const minutes = Math.floor((ms % 3_600_000) / 60_000);
  const seconds = Math.floor((ms % 60_000) / 1000);
  return { past, days, hours, minutes, seconds };
}

const pad = (n: number) => String(n).padStart(2, "0");

/**
 * A dockable live-countdown panel pinned to the LEFT edge of the screen.
 * Minimized = a slim vertical tab; expanded = a drawer with a big ticking timer per
 * pinned countdown (updates every second). Only shown to signed-in users. Reuses the
 * same pins as the Deadlines page via the /countdowns API.
 *
 * The target date is a stored given; the live math here is display-only (no deadline is
 * computed or adjusted — steering/deadline-tracker.md).
 */
export default function CountdownDock() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Countdown[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  const load = useCallback(() => {
    getCountdowns()
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoaded(true));
  }, []);

  // Load on mount + whenever a pin changes anywhere in the app.
  useEffect(() => {
    if (!user) return;
    load();
    return onCountdownsChanged(load);
  }, [user, load]);

  // Tick every second only while the panel is open (saves work when minimized).
  useEffect(() => {
    if (!open) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [open]);

  if (!user || !loaded) return null;

  const count = items.length;
  // Soonest upcoming (or least-overdue) first for the tab badge.
  const sorted = [...items].sort((a, b) => a.targetDate.localeCompare(b.targetDate));
  const soonest = sorted[0];
  const badge = soonest ? remaining(soonest.targetDate, now) : null;

  async function remove(id: string) {
    setItems((prev) => prev.filter((c) => c.id !== id));
    try {
      await deleteCountdown(id);
      emitCountdownsChanged();
    } catch {
      load();
    }
  }

  return (
    <div className={`cd-dock ${open ? "open" : ""}`}>
      {/* Minimized tab — always visible on the left edge */}
      {!open && (
        <button
          className="cd-tab"
          onClick={() => setOpen(true)}
          aria-label="Open countdown timers"
          title="Countdown timers"
        >
          <span className="cd-tab-icon"><ClockIcon size={20} /></span>
          <span className="cd-tab-text">Countdowns</span>
          {count > 0 && badge && (
            <span className="cd-tab-badge">
              {badge.past ? "due" : `${badge.days}d`}
            </span>
          )}
        </button>
      )}

      {/* Expanded drawer */}
      {open && (
        <div className="cd-drawer" role="dialog" aria-label="Countdown timers">
          <div className="cd-drawer-head">
            <strong><ClockIcon size={17} /> Your countdowns</strong>
            <button
              className="cd-collapse"
              onClick={() => setOpen(false)}
              aria-label="Minimize"
              title="Minimize"
            >
              <ChevronLeftIcon size={16} />
            </button>
          </div>

          {count === 0 ? (
            <p className="muted cd-empty">
              No countdowns yet. Open <strong>Deadlines</strong> and tap “Pin
              countdown” on any deadline, or add a custom one.
            </p>
          ) : (
            <div className="cd-list">
              {sorted.map((c) => {
                const d = parseISO(c.targetDate);
                const tier = getUrgencyTier(d, new Date());
                const r = remaining(c.targetDate, now);
                return (
                  <div className={`cd-item tier-border ${tier}`} key={c.id}>
                    <div className="cd-item-head">
                      <span className="cd-item-title" title={c.note ?? undefined}>
                        {c.title}
                      </span>
                      <button
                        className="countdown-remove"
                        onClick={() => remove(c.id)}
                        aria-label={`Remove ${c.title}`}
                        title="Remove"
                      >
                        <CloseIcon size={14} />
                      </button>
                    </div>

                    <div className={`cd-clock ${tier}`}>
                      <div className="cd-unit">
                        <span className="cd-num">{r.days}</span>
                        <span className="cd-lbl">days</span>
                      </div>
                      <span className="cd-sep">:</span>
                      <div className="cd-unit">
                        <span className="cd-num">{pad(r.hours)}</span>
                        <span className="cd-lbl">hrs</span>
                      </div>
                      <span className="cd-sep">:</span>
                      <div className="cd-unit">
                        <span className="cd-num">{pad(r.minutes)}</span>
                        <span className="cd-lbl">min</span>
                      </div>
                      <span className="cd-sep">:</span>
                      <div className="cd-unit">
                        <span className="cd-num">{pad(r.seconds)}</span>
                        <span className="cd-lbl">sec</span>
                      </div>
                    </div>

                    <div className="cd-item-foot muted">
                      {r.past ? "passed on " : "target "} {c.targetDate}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <p className="muted cd-foot-note">
            Estimates to help you organize — not legal advice. Verify with your DSO or an
            immigration attorney.
          </p>
        </div>
      )}
    </div>
  );
}
