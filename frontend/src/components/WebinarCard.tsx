import { useState } from "react";
import {
  formatLocal,
  type HostType,
  type Webinar,
} from "../api/webinars";

const HOST_LABEL: Record<HostType, string> = {
  official: "Official",
  verified_creator: "Verified Creator",
  community: "Community",
};

export default function WebinarCard({ webinar }: { webinar: Webinar }) {
  const [expanded, setExpanded] = useState(false);
  const long = webinar.description.length > 140;

  return (
    <div className="card hover webinar-card">
      <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
        <span className={`host-badge ${webinar.hostType}`}>
          {HOST_LABEL[webinar.hostType]}
        </span>
        <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
          {webinar.visaTypeTags.map((t) => (
            <span className="tag" key={t}>{t === "ALL" ? "All" : t.replace("_", " ")}</span>
          ))}
        </div>
      </div>

      <h3 style={{ margin: "10px 0 6px" }}>{webinar.title}</h3>
      <p className="muted" style={{ margin: "0 0 10px" }}>
        {webinar.hostName} · {formatLocal(webinar.startDateUtc)}
        {webinar.durationMinutes ? ` · ${webinar.durationMinutes} min` : ""}
      </p>

      <p style={{ marginTop: 0 }}>
        {expanded || !long
          ? webinar.description
          : webinar.description.slice(0, 140) + "… "}
        {long && (
          <button className="btn ghost" style={{ padding: "0 4px" }} onClick={() => setExpanded((e) => !e)}>
            {expanded ? "less" : "more"}
          </button>
        )}
      </p>

      <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
        <a className="btn" href={webinar.registrationUrl} target="_blank" rel="noreferrer">
          Register →
        </a>
      </div>
    </div>
  );
}
