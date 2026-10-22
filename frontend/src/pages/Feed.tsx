import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useCategories } from "../api/categories";
import { api } from "../api/client";
import type { NewsItem, Post } from "../api/types";
import Disclaimer from "../components/Disclaimer";
import NewsCarousel from "../components/NewsCarousel";
import PostCard from "../components/PostCard";
import { useAuth } from "../context/AuthContext";

export default function Feed() {
  const categories = useCategories();
  const { user } = useAuth();
  const [posts, setPosts] = useState<Post[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [filter, setFilter] = useState<string>("All");
  const [loading, setLoading] = useState(true);

  // Latest news for the carousel (personalized to the user's category by the API).
  useEffect(() => {
    api.get<NewsItem[]>("/news").then((r) => setNews(r.data)).catch(() => setNews([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = filter === "All" ? {} : { category: filter };
    api
      .get<Post[]>("/posts", { params })
      .then((r) => setPosts(r.data))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="container wide">
      <section style={{ padding: "6px 0 6px" }}>
        <h2 style={{ color: "var(--olive-dark)", margin: "0 0 4px" }}>
          Welcome back, {user?.username} 🦘
        </h2>
        <p className="muted" style={{ marginTop: 0 }}>
          Latest immigration news
          {user ? ` — your ${user.visa_category} updates first.` : "."}
        </p>
      </section>

      <NewsCarousel items={news} />
      <div className="row" style={{ justifyContent: "flex-end", marginBottom: 20 }}>
        <Link to="/news" className="btn ghost">See all news →</Link>
      </div>

      <div className="row" style={{ justifyContent: "space-between", marginBottom: 16 }}>
        <h2 style={{ color: "var(--olive-dark)", margin: 0 }}>Community questions</h2>
        {user && (
          <Link to="/new" className="btn pink" style={{ whiteSpace: "nowrap" }}>
            + Ask a question
          </Link>
        )}
      </div>

      <select
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        style={{ maxWidth: 220 }}
      >
        <option value="All">All categories</option>
        {categories.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>

      <Disclaimer />

      {loading ? (
        <p className="muted">Loading…</p>
      ) : posts.length === 0 ? (
        <div className="card">
          <p>No questions yet in this category.</p>
          <Link to="/new" className="btn">Be the first to ask</Link>
        </div>
      ) : (
        <div className="stack">
          {posts.map((p) => (
            <PostCard key={p.id} post={p} />
          ))}
        </div>
      )}
    </div>
  );
}
