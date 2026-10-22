import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCategories } from "../api/categories";
import { api } from "../api/client";
import type { Moderation, Post } from "../api/types";

export default function NewPost() {
  const categories = useCategories();
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState("OPT");
  const [anon, setAnon] = useState(false);
  const [mod, setMod] = useState<Moderation | null>(null);
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Gatekeeper preview — runs the AI check WITHOUT posting (soft-warn UX).
  async function runGatekeeper() {
    if (!title.trim() || !body.trim()) return;
    setChecking(true);
    try {
      const { data } = await api.post<Moderation>("/posts/moderate", {
        title,
        body,
        visa_category: category,
      });
      setMod(data);
      if (data.suggested_category && categories.includes(data.suggested_category)) {
        setCategory(data.suggested_category);
      }
    } finally {
      setChecking(false);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const { data } = await api.post<Post>("/posts", {
        title,
        body,
        visa_category: category,
        is_anonymous: anon,
      });
      navigate(`/posts/${data.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 640 }}>
      <h2>Ask the community</h2>
      <form onSubmit={submit} className="card">
        <label>Title</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={runGatekeeper}
          placeholder="e.g. How many OPT unemployment days do I have left?"
          required
        />

        <label>Details</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          onBlur={runGatekeeper}
          placeholder="Share your situation and what you're trying to figure out."
          required
        />

        {checking && <p className="muted">🦘 Visaroo is reviewing your post…</p>}

        {mod && (
          <div className={mod.warning ? "warn" : "ai-summary"}>
            {mod.warning ? (
              <p style={{ margin: 0 }}>{mod.warning}</p>
            ) : (
              <p style={{ margin: 0 }}>
                ✓ Looks on-topic. Suggested category: <strong>{mod.suggested_category}</strong>.
              </p>
            )}
            {mod.suggested_title && mod.suggested_title !== title && (
              <p style={{ marginBottom: 0 }}>
                Suggested title:{" "}
                <button
                  type="button"
                  className="btn ghost"
                  onClick={() => setTitle(mod.suggested_title)}
                >
                  “{mod.suggested_title}”
                </button>
              </p>
            )}
          </div>
        )}

        <label>Visa category</label>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <label className="row" style={{ fontWeight: 400 }}>
          <input
            type="checkbox"
            checked={anon}
            onChange={(e) => setAnon(e.target.checked)}
            style={{ width: "auto", margin: 0 }}
          />
          Post anonymously
        </label>

        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? "Posting…" : "Post question"}
        </button>
      </form>
    </div>
  );
}
