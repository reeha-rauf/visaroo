import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { NewsItem } from "../api/types";
import Disclaimer from "../components/Disclaimer";
import { CategoryIcon, RefreshIcon } from "../components/icons";
import { useAuth } from "../context/AuthContext";
import { categoryTheme } from "../lib/categoryTheme";

export default function News() {
  const { user } = useAuth();
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const { data } = await api.get<NewsItem[]>("/news");
      setItems(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function refresh() {
    setRefreshing(true);
    try {
      await api.post("/news/refresh");
      await load();
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="container wide">
      <div className="page-head">
        <h1>Immigration news</h1>
        <p>
          Official updates, summarized in plain language
          {user ? ` — your ${user.visa_category} news first.` : "."}
        </p>
      </div>

      <div className="row" style={{ justifyContent: "flex-end", marginBottom: 12 }}>
        <button className="btn secondary icon-btn" onClick={refresh} disabled={refreshing}>
          <RefreshIcon size={15} /> {refreshing ? "Fetching…" : "Refresh news"}
        </button>
      </div>

      <Disclaimer />

      {loading ? (
        <p className="muted">Loading…</p>
      ) : items.length === 0 ? (
        <div className="card">
          <p>No news yet. Click “Refresh news” to pull the latest from official sources.</p>
        </div>
      ) : (
        <div
          className="stack"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: 18,
          }}
        >
          {items.map((n) => {
            const theme = categoryTheme(n.visa_category);
            return (
              <div
                className="card hover"
                key={n.id}
                style={{ padding: 0, overflow: "hidden", marginBottom: 0 }}
              >
                <div
                  style={{
                    background: n.image_url
                      ? `center / cover no-repeat url("${n.image_url}")`
                      : theme.gradient,
                    height: 120,
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0 18px",
                  }}
                >
                  {n.image_url && (
                    <div
                      style={{
                        position: "absolute",
                        inset: 0,
                        background:
                          "linear-gradient(180deg, rgba(0,0,0,0.05), rgba(0,0,0,0.35))",
                      }}
                    />
                  )}
                  <span
                    className="tag"
                    style={{ background: "rgba(255,255,255,0.92)", border: "none", position: "relative" }}
                  >
                    {n.visa_category}
                  </span>
                  {!n.image_url && (
                    <span style={{ color: "#fff", display: "inline-flex", filter: "drop-shadow(0 4px 10px rgba(0,0,0,0.25))" }}>
                      <CategoryIcon icon={theme.icon} size={40} />
                    </span>
                  )}
                </div>
                <div style={{ padding: "16px 20px 20px" }}>
                  <span className="news-source">
                    {n.source === "federal_register" ? "Federal Register" : "Official RSS"}
                  </span>
                  <h3 style={{ margin: "6px 0 8px", fontSize: 17 }}>{n.title}</h3>
                  <p className="muted" style={{ marginTop: 0 }}>{n.summary}</p>
                  <a href={n.url} target="_blank" rel="noreferrer" style={{ fontWeight: 700 }}>
                    Read the full source →
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
