import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { PostDetail as PostDetailType } from "../api/types";
import Disclaimer from "../components/Disclaimer";
import VoteButtons from "../components/VoteButtons";
import { useAuth } from "../context/AuthContext";

export default function PostDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [post, setPost] = useState<PostDetailType | null>(null);
  const [body, setBody] = useState("");
  const [anon, setAnon] = useState(false);

  async function load() {
    const { data } = await api.get<PostDetailType>(`/posts/${id}`);
    setPost(data);
  }

  useEffect(() => {
    load();
  }, [id]);

  async function submitAnswer(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim()) return;
    await api.post(`/posts/${id}/answers`, { body, is_anonymous: anon });
    setBody("");
    setAnon(false);
    await load();
  }

  async function markBest(answerId: number) {
    await api.post(`/answers/${answerId}/best`);
    await load();
  }

  if (!post) return <div className="container">Loading…</div>;

  return (
    <div className="container">
      <div className="card">
        <span className="tag">{post.visa_category}</span>
        <h2 style={{ marginBottom: 6 }}>{post.title}</h2>
        <p>{post.body}</p>
        <div className="row">
          <VoteButtons targetType="post" targetId={post.id} score={post.score} />
          <span className="muted">by {post.author}</span>
        </div>
      </div>

      <Disclaimer />

      <h3>{post.answers.length} answer{post.answers.length !== 1 ? "s" : ""}</h3>
      {post.answers.map((a) => (
        <div className="card" key={a.id}>
          {a.is_best && <span className="best-badge">✓ Best answer</span>}
          <p style={{ marginTop: a.is_best ? 8 : 0 }}>{a.body}</p>
          <div className="row">
            <VoteButtons targetType="answer" targetId={a.id} score={a.score} />
            <span className="muted">by {a.author}</span>
            {user && !a.is_best && (
              <button className="btn ghost" onClick={() => markBest(a.id)}>
                Mark as best
              </button>
            )}
          </div>
        </div>
      ))}

      {user ? (
        <form onSubmit={submitAnswer} className="card">
          <label>Share your experience</label>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} />
          <label className="row" style={{ fontWeight: 400 }}>
            <input
              type="checkbox"
              checked={anon}
              onChange={(e) => setAnon(e.target.checked)}
              style={{ width: "auto", margin: 0 }}
            />
            Post anonymously
          </label>
          <button className="btn" type="submit">Post answer</button>
        </form>
      ) : (
        <p className="muted">Log in to answer.</p>
      )}
    </div>
  );
}
