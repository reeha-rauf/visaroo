import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { ComputedDeadline } from "../utils/computeDeadlines";
import { EditIcon, PinIcon } from "./icons";

interface Props {
  deadline: ComputedDeadline;
  onOverride: (id: string, iso: string) => Promise<void> | void;
  onResetOverride: (id: string) => Promise<void> | void;
  /** Pin this deadline as a persistent countdown. Omit to hide the pin action. */
  onPin?: (deadline: ComputedDeadline) => Promise<void> | void;
  /** Whether this deadline is already pinned as a countdown. */
  isPinned?: boolean;
}

const TIER_LABEL: Record<string, string> = {
  critical: "Critical",
  warning: "Warning",
  upcoming: "Upcoming",
  ok: "OK",
  expired: "Expired",
  na: "N/A",
};

function daysLabel(d: ComputedDeadline): string {
  if (d.daysRemaining === null) return "";
  if (d.daysRemaining < 0) return `${Math.abs(d.daysRemaining)}d ago`;
  if (d.daysRemaining === 0) return "today";
  return `in ${d.daysRemaining}d`;
}

export default function DeadlineCard({
  deadline,
  onOverride,
  onResetOverride,
  onPin,
  isPinned = false,
}: Props) {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [pinning, setPinning] = useState(false);
  const [draft, setDraft] = useState(
    deadline.date ? deadline.date.toISOString().slice(0, 10) : "",
  );

  const missing = deadline.date === null;
  const iso = deadline.date ? deadline.date.toISOString().slice(0, 10) : null;

  function askAboutThis() {
    const q = `What does the "${deadline.label}" deadline mean${iso ? ` (mine is ${iso})` : ""}?`;
    navigate(`/search?q=${encodeURIComponent(q)}`);
  }

  async function saveOverride() {
    if (!draft) return;
    await onOverride(deadline.id, draft);
    setEditing(false);
  }

  async function pin() {
    if (!onPin || isPinned) return;
    setPinning(true);
    try {
      await onPin(deadline);
    } finally {
      setPinning(false);
    }
  }

  return (
    <div className={`card deadline-card tier-border ${deadline.tier}`}>
      <div
        className="row deadline-head"
        style={{ justifyContent: "space-between", cursor: "pointer" }}
        onClick={() => setOpen((o) => !o)}
      >
        <div>
          <div className="row" style={{ gap: 8 }}>
            <strong>{deadline.label}</strong>
            {deadline.isOverridden && (
              <span className="override-badge">Overridden <EditIcon size={11} /></span>
            )}
          </div>
          {missing ? (
            <span className="muted">Complete your profile to see this deadline</span>
          ) : (
            <span className="muted">{iso}</span>
          )}
        </div>
        <div className="row" style={{ gap: 10 }}>
          {!missing && (
            <>
              <span className={`tier-pill ${deadline.tier}`}>{daysLabel(deadline)}</span>
              <span className={`tier-dot ${deadline.tier}`} title={TIER_LABEL[deadline.tier]} />
            </>
          )}
          {missing && <span className="tier-pill na">N/A</span>}
        </div>
      </div>

      {open && (
        <div className="deadline-body">
          {missing ? (
            <p className="muted" style={{ marginBottom: 0 }}>
              This deadline needs more profile data.{" "}
              <a href="/profile">Complete your profile →</a>
            </p>
          ) : (
            <>
              <p>{deadline.description}</p>
              <p className="consequence"><strong>If missed:</strong> {deadline.consequence}</p>
              {deadline.regulationCite && (
                <p className="muted">Source: {deadline.regulationCite}</p>
              )}
              <div className="row" style={{ gap: 10, flexWrap: "wrap", marginTop: 8 }}>
                {deadline.officialUrl && (
                  <a className="btn secondary" href={deadline.officialUrl} target="_blank" rel="noreferrer">
                    Official guidance →
                  </a>
                )}
                <button className="btn ghost" onClick={askAboutThis}>Ask about this</button>
                {onPin && !missing && (
                  isPinned ? (
                    <span className="override-badge" title="This deadline is pinned to your countdowns">
                      <PinIcon size={11} /> Pinned
                    </span>
                  ) : (
                    <button className="btn ghost icon-btn" onClick={pin} disabled={pinning}>
                      <PinIcon size={14} /> {pinning ? "Pinning…" : "Pin countdown"}
                    </button>
                  )
                )}
                {!editing && (
                  <button className="btn ghost icon-btn" onClick={() => setEditing(true)}>
                    <EditIcon size={14} /> Override date
                  </button>
                )}
                {deadline.isOverridden && (
                  <button className="btn ghost" onClick={() => onResetOverride(deadline.id)}>
                    Reset to calculated
                  </button>
                )}
              </div>

              {editing && (
                <div className="row" style={{ gap: 10, marginTop: 10, flexWrap: "wrap" }}>
                  <input
                    type="date"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    style={{ margin: 0, maxWidth: 200 }}
                  />
                  <button className="btn" onClick={saveOverride} disabled={!draft}>Save</button>
                  <button className="btn ghost" onClick={() => setEditing(false)}>Cancel</button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
