import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiUrl, getToken } from "../api/client";
import {
  LEAD_TIME_OPTIONS,
  PETITION_STATUSES,
  STATUS_PHASES,
  STEM_OPT_STATUSES,
  VISA_TYPES,
  cleanProfile,
  deleteProfile,
  getProfile,
  putProfile,
  type Profile as ProfileT,
  type ProfileOut,
} from "../api/profile";
import { DownloadIcon } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import { dateBadge } from "../lib/dateBadge";

const DATE_FIELDS: { key: keyof ProfileT; label: string }[] = [
  { key: "programStartDate", label: "Program start" },
  { key: "programEndDate", label: "Program end" },
  { key: "i20ExpiryDate", label: "I-20 expiry" },
  { key: "eadStartDate", label: "EAD start" },
  { key: "eadEndDate", label: "EAD end" },
  { key: "i94ExpiryDate", label: "I-94 expiry" },
  { key: "visaStampExpiry", label: "Visa stamp expiry" },
  { key: "portOfEntryDate", label: "Port of entry" },
  { key: "nextSevpReportingDate", label: "Next SEVP reporting" },
  { key: "nextRenewalReminder", label: "Renewal reminder" },
  { key: "gracePeriodEndDate", label: "Grace period end (override)" },
];

function Badge({ iso }: { iso?: string | null }) {
  const b = dateBadge(iso);
  if (!iso) return <span className="muted">not set</span>;
  const cls =
    b.tone === "red" ? "deadline red"
    : b.tone === "amber" ? "deadline amber"
    : b.tone === "grey" ? "deadline grey"
    : "deadline";
  return (
    <span className={cls}>
      {iso} · {b.label}
    </span>
  );
}

export default function Profile() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [p, setP] = useState<ProfileOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    getProfile()
      .then((data) => {
        if (!data) {
          navigate("/onboarding");
          return;
        }
        setP(data);
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  function set<K extends keyof ProfileT>(key: K, value: ProfileT[K]) {
    setP((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function save() {
    if (!p) return;
    try {
      const updated = await putProfile(cleanProfile(p));
      setP(updated);
      await refresh();
      setSaved(true);
      setTimeout(() => setSaved(false), 1800);
    } catch (e: any) {
      alert(e?.response?.data?.detail ?? "Could not save.");
    }
  }

  function exportData() {
    // Hit the export endpoint with the auth token and trigger a download.
    fetch(apiUrl("/profile/export"), {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "visaroo-profile.json";
        a.click();
        URL.revokeObjectURL(url);
      });
  }

  async function doDelete() {
    await deleteProfile();
    setConfirmDelete(false);
    navigate("/onboarding");
  }

  if (loading) return <div className="container">Loading…</div>;
  if (!p) return null;

  const phases = STATUS_PHASES[p.visaType] ?? ["active"];
  const isOpt = p.visaType === "OPT" || p.visaType === "STEM_OPT";
  const isH1b = p.visaType === "H-1B";
  const cap = p.computed.unemploymentCap ?? 0;
  const remaining = p.computed.unemploymentDaysRemaining ?? cap;
  const used = cap ? cap - remaining : 0;

  return (
    <div className="container">
      <div className="page-head row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>Your profile</h1>
          <p>{user?.email}</p>
        </div>
        <div className="row">
          {saved && <span className="muted">✓ Saved</span>}
          <button className="btn" onClick={save}>Save changes</button>
        </div>
      </div>

      {/* Identity + visa status */}
      <div className="card">
        <h3>Identity & visa status</h3>
        <label>Full name</label>
        <input value={p.fullName} onChange={(e) => set("fullName", e.target.value)} />
        <div className="grid-2">
          <div>
            <label>Country of origin</label>
            <input value={p.countryOfOrigin ?? ""} onChange={(e) => set("countryOfOrigin", e.target.value)} />
          </div>
          <div>
            <label>University / employer</label>
            <input value={p.universityOrEmployer ?? ""} onChange={(e) => set("universityOrEmployer", e.target.value)} />
          </div>
        </div>
        <div className="grid-2">
          <div>
            <label>Visa type</label>
            <select
              value={p.visaType}
              onChange={(e) => {
                const vt = e.target.value;
                set("visaType", vt);
                set("statusPhase", (STATUS_PHASES[vt] ?? ["active"])[0]);
              }}
            >
              {VISA_TYPES.map((v) => <option key={v} value={v}>{v.replace("_", " ")}</option>)}
            </select>
          </div>
          <div>
            <label>Status phase</label>
            <select value={p.statusPhase} onChange={(e) => set("statusPhase", e.target.value)}>
              {phases.map((ph) => <option key={ph} value={ph}>{ph}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* OPT / STEM OPT */}
      {isOpt && (
        <div className="card">
          <h3>OPT / STEM OPT</h3>
          <div className="grid-2">
            <div>
              <label>Employer name</label>
              <input value={p.employerName ?? ""} onChange={(e) => set("employerName", e.target.value)} />
            </div>
            <div>
              <label>Employer E-Verify # (encrypted)</label>
              <input value={p.employerEVerify ?? ""} onChange={(e) => set("employerEVerify", e.target.value)} />
            </div>
          </div>
          <div className="grid-2">
            <div>
              <label>STEM OPT status</label>
              <select value={p.stemOptStatus ?? ""} onChange={(e) => set("stemOptStatus", e.target.value || null)}>
                <option value="">—</option>
                {STEM_OPT_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="check" style={{ marginTop: 28 }}>
                <input type="checkbox" checked={!!p.i983OnFile} onChange={(e) => set("i983OnFile", e.target.checked)} />
                I-983 training plan on file
              </label>
            </div>
          </div>
          <label>Unemployment days used</label>
          <input
            type="number" min={0} max={150}
            value={p.unemploymentDaysUsed ?? ""}
            onChange={(e) => set("unemploymentDaysUsed", e.target.value === "" ? null : Number(e.target.value))}
          />
          {cap > 0 && (
            <div className="counter">
              <div className="counter-bar">
                <div
                  className="counter-fill"
                  style={{ width: `${Math.min(100, (used / cap) * 100)}%` }}
                />
              </div>
              <span className="muted">{remaining} of {cap} unemployment days remaining</span>
            </div>
          )}
        </div>
      )}

      {/* H-1B */}
      {isH1b && (
        <div className="card">
          <h3>H-1B</h3>
          <div className="grid-2">
            <div>
              <label>Petition receipt # (encrypted)</label>
              <input value={p.petitionReceiptNumber ?? ""} onChange={(e) => set("petitionReceiptNumber", e.target.value)} />
            </div>
            <div>
              <label>Petition status</label>
              <select value={p.petitionStatus ?? ""} onChange={(e) => set("petitionStatus", e.target.value || null)}>
                <option value="">—</option>
                {PETITION_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
              </select>
            </div>
          </div>
          <div className="grid-2">
            <div>
              <label>Employer EIN (encrypted)</label>
              <input value={p.employerEIN ?? ""} onChange={(e) => set("employerEIN", e.target.value)} />
            </div>
            <div>
              <label className="check" style={{ marginTop: 28 }}>
                <input type="checkbox" checked={!!p.h1bTransferInProgress} onChange={(e) => set("h1bTransferInProgress", e.target.checked)} />
                Transfer in progress
              </label>
            </div>
          </div>
        </div>
      )}

      {/* Dates */}
      <div className="card">
        <h3>Key dates</h3>
        <div className="grid-2">
          {DATE_FIELDS.map(({ key, label }) => (
            <div key={key as string}>
              <label>{label}</label>
              <input
                type="date"
                value={(p[key] as string) ?? ""}
                onChange={(e) => set(key, e.target.value as any)}
              />
              <div style={{ marginTop: -6, marginBottom: 10 }}>
                <Badge iso={p[key] as string} />
              </div>
            </div>
          ))}
        </div>

        <h4 style={{ color: "var(--olive-dark)" }}>Computed estimates</h4>
        <p className="muted" style={{ marginTop: 0 }}>Calculated from your dates — estimates, not legal guarantees.</p>
        <ul className="computed-list">
          <li>OPT application window opens: <Badge iso={p.computed.optApplicationWindowOpens} /></li>
          <li>OPT application deadline: <Badge iso={p.computed.optApplicationDeadline} /></li>
          <li>STEM filing window: <Badge iso={p.computed.stemFilingWindowStart} /> → <Badge iso={p.computed.stemFilingWindowEnd} /></li>
          <li>Grace period end: <Badge iso={p.computed.gracePeriodEnd} /></li>
        </ul>
      </div>

      {/* Travel */}
      <div className="card">
        <h3>Travel</h3>
        <label>Last US entry date</label>
        <input type="date" value={p.lastUsEntryDate ?? ""} onChange={(e) => set("lastUsEntryDate", e.target.value)} />
        <label>Recent countries visited (comma separated)</label>
        <input
          value={(p.recentCountriesVisited ?? []).join(", ")}
          onChange={(e) =>
            set("recentCountriesVisited", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))
          }
        />
        {p.visaType === "H-4" && (
          <label className="check">
            <input type="checkbox" checked={!!p.advanceParoleFiled} onChange={(e) => set("advanceParoleFiled", e.target.checked)} />
            Advance parole filed
          </label>
        )}
      </div>

      {/* Contacts */}
      <div className="card">
        <h3>DSO / attorney</h3>
        <div className="grid-2">
          <div>
            <label>DSO name</label>
            <input value={p.dsoName ?? ""} onChange={(e) => set("dsoName", e.target.value)} />
          </div>
          <div>
            <label>DSO email</label>
            <input value={p.dsoEmail ?? ""} onChange={(e) => set("dsoEmail", e.target.value)} />
          </div>
        </div>
        <div className="grid-2">
          <div>
            <label>Attorney name</label>
            <input value={p.attorneyName ?? ""} onChange={(e) => set("attorneyName", e.target.value)} />
          </div>
          <div>
            <label>Attorney email</label>
            <input value={p.attorneyEmail ?? ""} onChange={(e) => set("attorneyEmail", e.target.value)} />
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="card">
        <h3>Notifications</h3>
        <label className="check">
          <input
            type="checkbox"
            checked={p.notifications.emailEnabled}
            onChange={(e) => set("notifications", { ...p.notifications, emailEnabled: e.target.checked })}
          />
          Email alerts
        </label>
        <p className="muted" style={{ marginBottom: 6 }}>Deadline reminder lead times:</p>
        <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
          {LEAD_TIME_OPTIONS.map((d) => {
            const on = p.notifications.deadlineLeadTimeDays.includes(d);
            return (
              <button
                key={d} type="button"
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
      </div>

      {/* Privacy */}
      <div className="card">
        <h3>Privacy & AI personalization</h3>
        <p className="muted" style={{ marginTop: 0 }}>
          Choose which parts of your profile the AI may use to tailor answers. Toggled-off
          sections are never sent to the AI.
        </p>
        {(["visaStatus", "keyDates", "travel", "employer"] as const).map((k) => (
          <label className="check" key={k}>
            <input
              type="checkbox"
              checked={p.aiPersonalizationFields[k]}
              onChange={(e) =>
                set("aiPersonalizationFields", { ...p.aiPersonalizationFields, [k]: e.target.checked })
              }
            />
            Use my {k === "visaStatus" ? "visa status" : k === "keyDates" ? "key dates" : k}
          </label>
        ))}

        <div className="row" style={{ marginTop: 16, gap: 10 }}>
          <button className="btn secondary icon-btn" onClick={exportData}>
            <DownloadIcon size={15} /> Export my data (JSON)
          </button>
          <button className="btn pink" onClick={() => setConfirmDelete(true)}>Delete account data</button>
        </div>
      </div>

      {/* Second save button so users don't have to scroll back to the top. */}
      <div className="row" style={{ justifyContent: "flex-end", gap: 12, marginBottom: 40 }}>
        {saved && <span className="muted">✓ Saved</span>}
        <button className="btn" onClick={save}>Save changes</button>
      </div>

      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Delete your profile data?</h3>
            <p className="muted">
              This permanently removes all your stored profile data. This cannot be undone.
            </p>
            <div className="row" style={{ justifyContent: "flex-end", gap: 10 }}>
              <button className="btn secondary" onClick={() => setConfirmDelete(false)}>Cancel</button>
              <button className="btn pink" onClick={doDelete}>Delete everything</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
