import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LEAD_TIME_OPTIONS,
  STATUS_PHASES,
  VISA_TYPES,
  cleanProfile,
  emptyProfile,
  putProfile,
  type Profile,
} from "../api/profile";
import { useAuth } from "../context/AuthContext";

// Which key-date fields to show per visa type (design.md conditional rendering).
function dateFieldsFor(visaType: string): { key: keyof Profile; label: string }[] {
  const common: { key: keyof Profile; label: string }[] = [
    { key: "portOfEntryDate", label: "Port of entry date" },
    { key: "visaStampExpiry", label: "Visa stamp expiry" },
  ];
  if (visaType === "F-1") {
    return [
      { key: "programStartDate", label: "Program start (I-20)" },
      { key: "programEndDate", label: "Program end (I-20)" },
      { key: "i20ExpiryDate", label: "I-20 expiry" },
      ...common,
    ];
  }
  if (visaType === "OPT" || visaType === "STEM_OPT") {
    return [
      { key: "programEndDate", label: "Program end date" },
      { key: "eadStartDate", label: "EAD start date" },
      { key: "eadEndDate", label: "EAD end date" },
      ...common,
    ];
  }
  if (visaType === "H-1B") {
    return [{ key: "i94ExpiryDate", label: "I-94 expiration" }, ...common];
  }
  return common;
}

export default function Onboarding() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [step, setStep] = useState(1);
  const [p, setP] = useState<Profile>(emptyProfile());
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function set<K extends keyof Profile>(key: K, value: Profile[K]) {
    setP((prev) => ({ ...prev, [key]: value }));
  }

  const phases = STATUS_PHASES[p.visaType] ?? ["active"];

  async function finish() {
    setSaving(true);
    setError(null);
    try {
      await putProfile(cleanProfile(p));
      await refresh();
      navigate("/profile");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Could not save your profile.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="container narrow">
      <div className="page-head">
        <h1>Set up your profile 🦘</h1>
        <p>Step {step} of 3 — this personalizes your deadlines and news.</p>
      </div>

      <div className="onboard-progress">
        {[1, 2, 3].map((n) => (
          <span key={n} className={n <= step ? "dot active" : "dot"} />
        ))}
      </div>

      {error && <div className="warn">{error}</div>}

      {step === 1 && (
        <div className="card">
          <h3>Your visa status</h3>
          <label>Full name</label>
          <input value={p.fullName} onChange={(e) => set("fullName", e.target.value)} />
          <label>Visa type</label>
          <select
            value={p.visaType}
            onChange={(e) => {
              const vt = e.target.value;
              set("visaType", vt);
              // reset phase to first valid option for the new type
              set("statusPhase", (STATUS_PHASES[vt] ?? ["active"])[0]);
            }}
          >
            {VISA_TYPES.map((v) => (
              <option key={v} value={v}>{v.replace("_", " ")}</option>
            ))}
          </select>
          <label>Current phase</label>
          <select value={p.statusPhase} onChange={(e) => set("statusPhase", e.target.value)}>
            {phases.map((ph) => (
              <option key={ph} value={ph}>{ph}</option>
            ))}
          </select>
          <div className="row" style={{ justifyContent: "flex-end" }}>
            <button className="btn" onClick={() => setStep(2)}>Next</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h3>Key dates</h3>
          <p className="muted" style={{ marginTop: 0 }}>
            Add at least one. You can edit or add more later. Dates use YYYY-MM-DD.
          </p>
          {dateFieldsFor(p.visaType).map(({ key, label }) => (
            <div key={key as string}>
              <label>{label}</label>
              <input
                type="date"
                value={(p[key] as string) ?? ""}
                onChange={(e) => set(key, e.target.value as any)}
              />
            </div>
          ))}
          {(p.visaType === "OPT" || p.visaType === "STEM_OPT") && (
            <>
              <label>Unemployment days used ({p.visaType === "STEM_OPT" ? "0–150" : "0–90"})</label>
              <input
                type="number"
                min={0}
                max={150}
                value={p.unemploymentDaysUsed ?? ""}
                onChange={(e) =>
                  set(
                    "unemploymentDaysUsed",
                    e.target.value === "" ? null : Number(e.target.value)
                  )
                }
              />
            </>
          )}
          <div className="row" style={{ justifyContent: "space-between" }}>
            <button className="btn secondary" onClick={() => setStep(1)}>Back</button>
            <button className="btn" onClick={() => setStep(3)}>Next</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h3>Notifications</h3>
          <label className="check">
            <input
              type="checkbox"
              checked={p.notifications.emailEnabled}
              onChange={(e) =>
                set("notifications", {
                  ...p.notifications,
                  emailEnabled: e.target.checked,
                })
              }
            />
            Email alerts
          </label>

          <p className="muted" style={{ marginBottom: 6 }}>Remind me before deadlines:</p>
          <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
            {LEAD_TIME_OPTIONS.map((d) => {
              const on = p.notifications.deadlineLeadTimeDays.includes(d);
              return (
                <button
                  key={d}
                  type="button"
                  className={on ? "chip-btn active" : "chip-btn"}
                  onClick={() =>
                    set("notifications", {
                      ...p.notifications,
                      deadlineLeadTimeDays: on
                        ? p.notifications.deadlineLeadTimeDays.filter((x) => x !== d)
                        : [...p.notifications.deadlineLeadTimeDays, d],
                    })
                  }
                >
                  {d} days
                </button>
              );
            })}
          </div>

          <div className="row" style={{ justifyContent: "space-between", marginTop: 16 }}>
            <button className="btn secondary" onClick={() => setStep(2)}>Back</button>
            <button className="btn" onClick={finish} disabled={saving}>
              {saving ? "Saving…" : "Finish"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
