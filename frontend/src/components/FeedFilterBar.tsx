import { FEED_VISA_TAGS, STATUS_FILTERS } from "../api/creatorPosts";

interface Props {
  visaType: string;
  statusLabel: string;
  onVisaChange: (v: string) => void;
  onStatusChange: (s: string) => void;
}

export default function FeedFilterBar({
  visaType,
  statusLabel,
  onVisaChange,
  onStatusChange,
}: Props) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="row" style={{ flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
        {FEED_VISA_TAGS.map((tag) => (
          <button
            key={tag}
            type="button"
            className={visaType === tag ? "chip-btn active" : "chip-btn"}
            onClick={() => onVisaChange(tag)}
          >
            {tag === "ALL" ? "All" : tag.replace("_", " ")}
          </button>
        ))}
      </div>
      <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
        {STATUS_FILTERS.map((s) => (
          <button
            key={s.value || "all"}
            type="button"
            className={statusLabel === s.value ? "chip-btn active" : "chip-btn"}
            onClick={() => onStatusChange(s.value)}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
