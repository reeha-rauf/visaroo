import { useState } from "react";
import {
  daysRemaining,
  getUrgencyTier,
  sevpDeadline,
} from "../utils/deadlineCalculations";

interface Props {
  lastReportableEventDate?: string | null;
  /** Persist a change: set an event date, or clear it (reported). */
  onUpdate: (patch: {
    lastReportableEventDate?: string | null;
    lastSevpReportedDate?: string | null;
  }) => Promise<void> | void;
}

/**
 * SEVP reporting countdown (REQ-4): a reportable change must be reported within 10 days.
 * Shows "no pending report", or a countdown to eventDate + 10, with mark-as-reported.
 */
export default function SevpReportingCard({
  lastReportableEventDate,
  onUpdate,
}: Props) {
  const [picking, setPicking] = useState(false);
  const [eventDate, setEventDate] = useState("");
  const [busy, setBusy] = useState(false);

  const deadline = sevpDeadline(lastReportableEventDate);
  const today = new Date();
  const tier = getUrgencyTier(deadline, today);
  const days = daysRemaining(deadline, today);

  async function recordEvent() {
    if (!eventDate) return;
    setBusy(true);
    try {
      await onUpdate({ lastReportableEventDate: eventDate, lastSevpReportedDate: null });
      setPicking(false);
      setEventDate("");
    } finally {
      setBusy(false);
    }
  }

  async function markReported() {
    setBusy(true);
    try {
      await onUpdate({
        lastReportableEventDate: null,
        lastSevpReportedDate: new Date().toISOString().slice(0, 10),
      });
    } finally {
      setBusy(false);
    }
  }

  const hasPending = !!deadline;

  return (
    <div className={`card hover tier-border ${hasPending ? tier : "ok"}`}>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3 style={{ margin: 0 }}>SEVP reporting</h3>
        {hasPending ? (
          <span className={`tier-pill ${tier}`}>
            {days !== null && days >= 0 ? `report in ${days} day${days === 1 ? "" : "s"}` : "overdue"}
          </span>
        ) : (
          <span className="tier-pill ok">No pending report</span>
        )}
      </div>

      {hasPending ? (
        <>
          <p className="muted" style={{ marginBottom: 10 }}>
            You logged a reportable change. SEVP must be updated by{" "}
            <strong>{deadline!.toISOString().slice(0, 10)}</strong> (within 10 days).
          </p>
          <button className="btn" onClick={markReported} disabled={busy}>
            Mark as reported
          </button>
        </>
      ) : (
        <>
          <p className="muted" style={{ marginBottom: 10 }}>
            Report employer, address, program, or employment changes within 10 days.
          </p>
          {!picking ? (
            <button className="btn secondary" onClick={() => setPicking(true)}>
              I had a reportable event
            </button>
          ) : (
            <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
              <input
                type="date"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
                style={{ margin: 0, maxWidth: 200 }}
              />
              <button className="btn" onClick={recordEvent} disabled={busy || !eventDate}>
                Set deadline
              </button>
              <button className="btn ghost" onClick={() => setPicking(false)}>
                Cancel
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
