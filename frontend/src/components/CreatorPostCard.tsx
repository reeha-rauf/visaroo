import { useEffect, useRef, useState } from "react";
import {
  getCreatorPost,
  STATUS_LABELS,
  timeAgo,
  type CreatorPost,
} from "../api/creatorPosts";
import { useAsk } from "../context/AskContext";

export default function CreatorPostCard({ post: initial }: { post: CreatorPost }) {
  const { openPanel } = useAsk();
  const [post, setPost] = useState(initial);
  const [expanded, setExpanded] = useState(false);
  const pollRef = useRef<number | null>(null);

  // Poll GET /creator-posts/:id every 5s while matchStatus is pending, up to 60s.
  useEffect(() => {
    if (post.matchStatus !== "pending") return;
    const started = Date.now();
    pollRef.current = window.setInterval(async () => {
      if (Date.now() - started > 60_000) {
        if (pollRef.current) window.clearInterval(pollRef.current);
        return;
      }
      try {
        const fresh = await getCreatorPost(post.id);
        if (fresh.matchStatus !== "pending") {
          setPost(fresh);
          if (pollRef.current) window.clearInterval(pollRef.current);
        }
      } catch {
        /* keep polling until the time budget runs out */
      }
    }, 5000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [post.id, post.matchStatus]);

  const status = STATUS_LABELS[post.statusLabel];

  function askAboutThis() {
    openPanel(`Does this affect me? ${post.headline}`);
  }

  return (
    <div className="card creator-post">
      <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
        <div className="row" style={{ gap: 8 }}>
          <span className="host-badge verified_creator">Verified Creator</span>
          <strong>{post.creatorDisplayName}</strong>
          <span className="muted">· {timeAgo(post.postedAt)}</span>
        </div>
      </div>

      <div className="row" style={{ gap: 8, flexWrap: "wrap", margin: "10px 0 6px" }}>
        <span className={`status-chip ${status.tone}`}>{status.text}</span>
        {post.visaTypeTags.map((t) => (
          <span className="tag" key={t}>{t === "ALL" ? "All" : t.replace("_", " ")}</span>
        ))}
      </div>

      <h3
        style={{ margin: "4px 0 8px", cursor: "pointer" }}
        onClick={() => setExpanded((e) => !e)}
      >
        {post.headline}
      </h3>

      <p className="muted" style={{ margin: "0 0 8px" }}>
        Source: <a href={post.sourceUrl} target="_blank" rel="noreferrer">{post.sourceLabel} →</a>
      </p>

      {/* Match status indicator */}
      {post.matchStatus === "pending" && (
        <p className="match-status pending">⏳ Checking official sources…</p>
      )}
      {post.matchStatus === "matched" && (
        <p className="match-status matched">
          ✓ Official source found
          {post.matchedDocumentUrl && (
            <>
              {" — "}
              <a href={post.matchedDocumentUrl} target="_blank" rel="noreferrer">
                {post.matchedDocumentTitle || "view document"}
              </a>
            </>
          )}
        </p>
      )}
      {post.matchStatus === "no_match" && (
        <p className="match-status no_match">⧖ Awaiting official confirmation</p>
      )}

      {expanded && (
        <div className="creator-post-body">
          <p>{post.body}</p>
          {(post.effectiveDate || post.expiryDate) && (
            <p className="muted">
              {post.effectiveDate && <>Effective: {post.effectiveDate}. </>}
              {post.expiryDate && <>Expires: {post.expiryDate}.</>}
            </p>
          )}
          <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
            <button className="btn" onClick={askAboutThis}>Does this affect me?</button>
            {post.matchStatus === "matched" && post.matchedDocumentUrl && (
              <a className="btn secondary" href={post.matchedDocumentUrl} target="_blank" rel="noreferrer">
                View official source
              </a>
            )}
          </div>
        </div>
      )}

      {/* Per-card trust label — required by steering, not optional. */}
      <p className="creator-disclaimer">
        Creator commentary — verify with official sources.
      </p>
    </div>
  );
}
