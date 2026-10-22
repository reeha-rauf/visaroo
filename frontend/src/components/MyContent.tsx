import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getMyAnswers,
  getMyPosts,
  myPostToCard,
  type MyAnswer,
  type MyPost,
} from "../api/me";
import { useAuth } from "../context/AuthContext";
import PostCard from "./PostCard";

type Tab = "questions" | "answers";

/** The user's own questions and answers, with Questions/Answers tabs.
 *  Set `heading={false}` when the page already provides its own title. */
export default function MyContent({ heading = true }: { heading?: boolean }) {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("questions");
  const [posts, setPosts] = useState<MyPost[]>([]);
  const [answers, setAnswers] = useState<MyAnswer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMyPosts(), getMyAnswers()])
      .then(([p, a]) => {
        setPosts(p);
        setAnswers(a);
      })
      .catch(() => {
        setPosts([]);
        setAnswers([]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="my-content">
      {heading && <h3 style={{ margin: "0 0 10px" }}>My posts & answers</h3>}

      <div className="my-tabs">
        <button
          type="button"
          className={tab === "questions" ? "my-tab active" : "my-tab"}
          onClick={() => setTab("questions")}
        >
          Questions ({posts.length})
        </button>
        <button
          type="button"
          className={tab === "answers" ? "my-tab active" : "my-tab"}
          onClick={() => setTab("answers")}
        >
          Answers ({answers.length})
        </button>
      </div>

      <div className="card my-tab-panel">
      {loading ? (
        <p className="muted" style={{ marginBottom: 0 }}>Loading…</p>
      ) : tab === "questions" ? (
        posts.length === 0 ? (
          <p className="muted my-empty">No questions yet.</p>
        ) : (
          <div className="stack" style={{ marginTop: 14 }}>
            {posts.map((p) => (
              <div key={p.id}>
                {p.is_anonymous && (
                  <span className="muted my-anon-note">Posted anonymously</span>
                )}
                <PostCard post={myPostToCard(p, user?.username ?? "You")} />
              </div>
            ))}
          </div>
        )
      ) : answers.length === 0 ? (
        <p className="muted my-empty">No answers yet.</p>
      ) : (
        <div className="stack" style={{ marginTop: 14 }}>
          {answers.map((a) => (
            <Link key={a.id} to={`/posts/${a.post_id}`} className="card hover my-answer-row">
              <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                <span className="muted">on “{a.post_title}”</span>
                <span className="row" style={{ gap: 8 }}>
                  {a.is_best && <span className="best-badge">★ Best answer</span>}
                  <span className="muted">▲ {a.score}</span>
                </span>
              </div>
              <p style={{ margin: "6px 0 0" }}>
                {a.body.length > 160 ? a.body.slice(0, 160) + "…" : a.body}
              </p>
            </Link>
          ))}
        </div>
      )}
      </div>
    </div>
  );
}
