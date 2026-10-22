import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { SearchResponse } from "../api/types";
import { ScaleIcon } from "../components/icons";

export default function Search() {
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function runQuery(q: string) {
    if (q.trim().length < 2) return;
    setLoading(true);
    try {
      const { data } = await api.post<SearchResponse>("/search", { query: q });
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  function run(e: React.FormEvent) {
    e.preventDefault();
    setParams(query.trim() ? { q: query.trim() } : {});
    runQuery(query);
  }

  // Auto-run when arriving with a ?q= param (e.g. from the top search bar).
  useEffect(() => {
    const q = params.get("q");
    if (q && q !== result?.query) {
      setQuery(q);
      runQuery(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  return (
    <div className="container">
      <div className="page-head">
        <h1>Search Visaroo</h1>
        <p>Ask a question — get an AI summary first, then the community posts behind it.</p>
      </div>

      <form onSubmit={run} className="row" style={{ marginBottom: 16 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Can I travel while my STEM OPT extension is pending?"
          style={{ margin: 0 }}
        />
        <button className="btn" type="submit" disabled={loading} style={{ whiteSpace: "nowrap" }}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {result && (
        <>
          <div className="ai-summary">
            <h3>🦘 AI summary</h3>
            <p style={{ marginBottom: 8 }}>{result.summary}</p>
            {result.grounded && (
              <p className="muted" style={{ margin: 0 }}>
                Based on {result.used_post_ids.length} community post
                {result.used_post_ids.length !== 1 ? "s" : ""}.
              </p>
            )}
          </div>
          <div className="disclaimer">{result.disclaimer}</div>
          <p style={{ marginTop: -4, marginBottom: 16 }}>
            <Link className="btn ghost icon-btn" to="/legal-help?prefill=true">
              <ScaleIcon size={15} /> Talk to a lawyer — get legal help →
            </Link>
          </p>

          <h3>Community posts</h3>
          {result.results.length === 0 ? (
            <p className="muted">No matching posts yet.</p>
          ) : (
            result.results.map((r) => (
              <div className="card" key={r.id}>
                <span className="tag">{r.visa_category}</span>
                <h4 style={{ margin: "8px 0" }}>
                  <Link to={`/posts/${r.id}`}>{r.title}</Link>
                </h4>
                <p className="muted" style={{ marginTop: 0 }}>{r.snippet}</p>
                <span className="muted">
                  score {r.score} · relevance {(r.similarity * 100).toFixed(0)}%
                </span>
              </div>
            ))
          )}
        </>
      )}
    </div>
  );
}
