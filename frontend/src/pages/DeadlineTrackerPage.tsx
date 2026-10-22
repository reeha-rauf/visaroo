import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiUrl, getToken } from "../api/client";
import {
  createCountdown,
  emitCountdownsChanged,
  getCountdowns,
  type Countdown,
} from "../api/countdowns";
import {
  cleanProfile,
  getProfile,
  putProfile,
  type ProfileOut,
} from "../api/profile";
import DeadlineCard from "../components/DeadlineCard";
import Disclaimer from "../components/Disclaimer";
import { DownloadIcon, PinIcon } from "../components/icons";
import PinnedCountdowns from "../components/PinnedCountdowns";
import SevpReportingCard from "../components/SevpReportingCard";
import UnemploymentCounter from "../components/UnemploymentCounter";
import type { ComputedDeadline } from "../utils/computeDeadlines";
import { computeDeadlines } from "../utils/computeDeadlines";
import { unemploymentCapFor } from "../utils/deadlineCalculations";

const SEVP_TYPES = ["F-1", "OPT", "STEM_OPT"];
const OPT_TYPES = ["OPT", "STEM_OPT"];

export default function DeadlineTrackerPage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProfileOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [showNa, setShowNa] = useState(false);

  // Pinned countdowns: track which deadline ids are pinned + a key to refresh the strip.
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());
  const [countdownKey, setCountdownKey] = useState(0);
  const [customTitle, setCustomTitle] = useState("");
  const [customDate, setCustomDate] = useState("");

  useEffect(() => {
    getProfile()
      .then((p) => {
        if (!p) {
          navigate("/onboarding");
          return;
        }
        setProfile(p);
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  const loadPinned = useCallback(() => {
    getCountdowns()
      .then((cs: Countdown[]) => {
        const ids = cs
          .map((c) => c.sourceDeadlineId)
          .filter((id): id is string => !!id);
        setPinnedIds(new Set(ids));
      })
      .catch(() => setPinnedIds(new Set()));
  }, []);

  useEffect(() => {
    loadPinned();
  }, [loadPinned]);

  async function pinDeadline(d: ComputedDeadline) {
    if (!d.date) return;
    await createCountdown({
      title: d.label,
      targetDate: d.date.toISOString().slice(0, 10),
      sourceDeadlineId: d.id,
    });
    setPinnedIds((prev) => new Set(prev).add(d.id));
    setCountdownKey((k) => k + 1);
    emitCountdownsChanged();
  }

  async function addCustomCountdown() {
    if (!customTitle.trim() || !customDate) return;
    await createCountdown({
      title: customTitle.trim(),
      targetDate: customDate,
    });
    setCustomTitle("");
    setCustomDate("");
    setCountdownKey((k) => k + 1);
    emitCountdownsChanged();
  }

  // When a countdown is removed from the strip, re-sync the pinned set so the matching
  // deadline card shows "Pin countdown" again.
  function onCountdownsChanged() {
    loadPinned();
    emitCountdownsChanged();
  }

  // Recompute on every render using the current date (REQ-2: no stale tiers).
  const deadlines = useMemo(
    () => (profile ? computeDeadlines(profile, new Date()) : []),
    [profile],
  );

  async function patchProfile(patch: Partial<ProfileOut>) {
    if (!profile) return;
    const next = { ...profile, ...patch } as ProfileOut;
    setProfile(next); // optimistic
    const saved = await putProfile(cleanProfile(next));
    setProfile(saved);
  }

  async function setOverride(id: string, iso: string) {
    const overrides = { ...(profile?.deadlineOverrides ?? {}), [id]: iso };
    await patchProfile({ deadlineOverrides: overrides });
  }

  async function resetOverride(id: string) {
    const overrides = { ...(profile?.deadlineOverrides ?? {}) };
    delete overrides[id];
    await patchProfile({
      deadlineOverrides: Object.keys(overrides).length ? overrides : null,
    });
  }

  function downloadIcs() {
    fetch(apiUrl("/deadlines/ics"), {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "visaroo-deadlines.ics";
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  if (loading) {
    return (
      <div className="container">
        <div className="page-head"><h1>Deadlines</h1></div>
        <div className="card skeleton" style={{ height: 90 }} />
        <div className="card skeleton" style={{ height: 90 }} />
        <div className="card skeleton" style={{ height: 90 }} />
      </div>
    );
  }

  if (!profile || !profile.visaType || profile.visaType === "Other") {
    return (
      <div className="container">
        <div className="page-head"><h1>Deadlines</h1></div>
        <div className="card">
          <p>Set up your profile with a visa type to see your deadlines.</p>
          <Link to="/profile" className="btn">Go to profile</Link>
        </div>
      </div>
    );
  }

  const visible = deadlines.filter((d) => (showNa ? true : d.tier !== "na"));
  const naCount = deadlines.filter((d) => d.tier === "na").length;
  const showUnemployment = OPT_TYPES.includes(profile.visaType);
  const showSevp = SEVP_TYPES.includes(profile.visaType);

  return (
    <div className="container">
      <div className="page-head row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>Your deadlines</h1>
          <p>Tracked for your {profile.visaType.replace("_", " ")} status.</p>
        </div>
        <button className="btn secondary icon-btn" onClick={downloadIcs}>
          <DownloadIcon size={15} /> Download calendar (.ics)
        </button>
      </div>

      <Disclaimer />

      <PinnedCountdowns
        refreshKey={countdownKey}
        variant="full"
        title="Your countdowns"
        emptyHint="Pin any deadline below (use “Pin countdown”) to keep a live timer here and on your home page."
        onChange={onCountdownsChanged}
      />

      <div className="card custom-countdown">
        <h4 style={{ margin: "0 0 8px" }}>Add a custom countdown</h4>
        <p className="muted" style={{ marginTop: 0 }}>
          Track any personal date — a biometrics appointment, a document deadline, a
          travel date.
        </p>
        <div className="row" style={{ gap: 10, flexWrap: "wrap", alignItems: "flex-end" }}>
          <div style={{ flex: "1 1 220px" }}>
            <label htmlFor="cd-title">Label</label>
            <input
              id="cd-title"
              value={customTitle}
              onChange={(e) => setCustomTitle(e.target.value)}
              placeholder="e.g. Biometrics appointment"
              maxLength={120}
              style={{ margin: 0 }}
            />
          </div>
          <div>
            <label htmlFor="cd-date">Date</label>
            <input
              id="cd-date"
              type="date"
              value={customDate}
              onChange={(e) => setCustomDate(e.target.value)}
              style={{ margin: 0, maxWidth: 200 }}
            />
          </div>
          <button
            className="btn icon-btn"
            onClick={addCustomCountdown}
            disabled={!customTitle.trim() || !customDate}
          >
            <PinIcon size={15} /> Add countdown
          </button>
        </div>
      </div>

      {showUnemployment && (
        <UnemploymentCounter
          daysUsed={profile.unemploymentDaysUsed ?? 0}
          cap={unemploymentCapFor(profile.visaType)}
          eadStartDate={profile.eadStartDate}
          onUpdate={(days) => patchProfile({ unemploymentDaysUsed: days })}
        />
      )}

      {showSevp && (
        <SevpReportingCard
          lastReportableEventDate={profile.lastReportableEventDate}
          onUpdate={(patch) => patchProfile(patch)}
        />
      )}

      <div className="stack">
        {visible.map((d) => (
          <DeadlineCard
            key={d.id}
            deadline={d}
            onOverride={setOverride}
            onResetOverride={resetOverride}
            onPin={pinDeadline}
            isPinned={pinnedIds.has(d.id)}
          />
        ))}
      </div>

      {naCount > 0 && (
        <button
          className="btn ghost"
          style={{ marginTop: 10 }}
          onClick={() => setShowNa((s) => !s)}
        >
          {showNa ? "Hide" : "Show"} {naCount} non-applicable deadline{naCount === 1 ? "" : "s"}
        </button>
      )}
    </div>
  );
}
