import { useState } from "react";
import {
  createCreatorPost,
  FEED_VISA_TAGS,
  STATUS_LABELS,
  type CreatorPost,
  type PostStatusLabel,
} from "../api/creatorPosts";

const STATUS_OPTIONS: PostStatusLabel[] = ["rumor_reported", "proposed", "final", "in_effect"];
const TAG_OPTIONS = FEED_VISA_TAGS.filter((t) => t); // includes ALL

interface Props {
  onClose: () => void;
  onCreated: (post: CreatorPost) => void;
}

export default function CreatePostModal({ onClose, onCreated }: Props) {
  const [headline, setHeadline] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [statusLabel, setStatusLabel] = useState<PostStatusLabel>("proposed");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceLabel, setSourceLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function toggleTag(tag: string) {
    setTags((prev) => (prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!headline.trim() || !body.trim() || tags.length === 0 || !sourceUrl.trim() || !sourceLabel.trim()) {
      setError("Headline, body, at least one visa tag, source URL, and source label are required.");
      return;
    }
    setSaving(true);
    try {
      const post = await createCreatorPost({
        headline,
        body,
        visaTypeTags: tags,
        statusLabel,
        sourceUrl,
        sourceLabel,
      });
      onCreated(post);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Could not create post.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" style={{ maxWidth: 560 }} onClick={(e) => e.stopPropagation()}>
        <h3>New creator post</h3>
        <form onSubmit={submit}>
          {error && <div className="warn">{error}</div>}

          <label>Headline ({headline.length}/120)</label>
          <input value={headline} maxLength={120} onChange={(e) => setHeadline(e.target.value)} />

          <label>Body ({body.length}/1000)</label>
          <textarea value={body} maxLength={1000} onChange={(e) => setBody(e.target.value)} />

          <label>Status label</label>
          <div className="row" style={{ flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
            {STATUS_OPTIONS.map((s) => (
              <button
                key={s}
                type="button"
                className={statusLabel === s ? `status-chip ${STATUS_LABELS[s].tone} selected` : `status-chip ${STATUS_LABELS[s].tone}`}
                onClick={() => setStatusLabel(s)}
              >
                {STATUS_LABELS[s].text}
              </button>
            ))}
          </div>

          <label>Visa type tags (select at least one)</label>
          <div className="row" style={{ flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
            {TAG_OPTIONS.map((t) => (
              <button
                key={t}
                type="button"
                className={tags.includes(t) ? "chip-btn active" : "chip-btn"}
                onClick={() => toggleTag(t)}
              >
                {t === "ALL" ? "All" : t.replace("_", " ")}
              </button>
            ))}
          </div>

          <label>Source label (e.g. "Federal Register")</label>
          <input value={sourceLabel} onChange={(e) => setSourceLabel(e.target.value)} />

          <label>Source URL</label>
          <input value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://…" />

          <div className="row" style={{ justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
            <button type="button" className="btn secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn" disabled={saving}>
              {saving ? "Posting…" : "Post"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
