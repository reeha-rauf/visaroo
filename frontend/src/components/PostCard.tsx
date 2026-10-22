import { Link } from "react-router-dom";
import type { Post } from "../api/types";
import { categoryTheme } from "../lib/categoryTheme";
import { CategoryIcon, ChatIcon } from "./icons";
import VoteButtons from "./VoteButtons";

export default function PostCard({ post }: { post: Post }) {
  const theme = categoryTheme(post.visa_category);
  return (
    <div className="card hover" style={{ display: "flex", gap: 16 }}>
      <div
        style={{
          width: 54,
          height: 54,
          borderRadius: 16,
          background: theme.gradient,
          display: "grid",
          placeItems: "center",
          color: "#fff",
          flexShrink: 0,
        }}
      >
        <CategoryIcon icon={theme.icon} size={26} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="tag">{post.visa_category}</span>
          {post.gatekeeper_flag && (
            <span className="flag">
              {post.gatekeeper_flag === "harmful" ? "flagged" : "off-topic"}
            </span>
          )}
        </div>
        <h3 className="post-card-title">
          <Link to={`/posts/${post.id}`}>{post.title}</Link>
        </h3>
        <p className="muted" style={{ marginTop: 0 }}>
          {post.body.length > 150 ? post.body.slice(0, 150) + "…" : post.body}
        </p>
        <div className="row">
          <VoteButtons targetType="post" targetId={post.id} score={post.score} />
          <span className="muted" style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <ChatIcon size={14} /> {post.answer_count} · by {post.author}
          </span>
        </div>
      </div>
    </div>
  );
}
