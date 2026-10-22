import { useEffect, useState } from "react";
import { getProfile } from "../api/profile";
import {
  FEED_VISA_TAGS,
  getCreatorPosts,
  type CreatorPost,
} from "../api/creatorPosts";
import CreatePostModal from "../components/CreatePostModal";
import CreatorPostCard from "../components/CreatorPostCard";
import Disclaimer from "../components/Disclaimer";
import FeedFilterBar from "../components/FeedFilterBar";
import { useAuth } from "../context/AuthContext";

function toTag(visaCategory?: string | null): string {
  if (!visaCategory) return "ALL";
  const t = visaCategory.replace("-", "_");
  return (FEED_VISA_TAGS as readonly string[]).includes(t) ? t : "ALL";
}

export default function CreatorFeedPage() {
  const { user } = useAuth();
  const [visaType, setVisaType] = useState("ALL");
  const [statusLabel, setStatusLabel] = useState("");
  const [ready, setReady] = useState(false);
  const [posts, setPosts] = useState<CreatorPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const isCreator = user?.role === "creator" || user?.role === "admin";

  // Default visa filter from the user's profile.
  useEffect(() => {
    if (!user) {
      setReady(true);
      return;
    }
    getProfile()
      .then((p) => setVisaType(toTag(p?.visaType ?? user.visa_category)))
      .catch(() => setVisaType(toTag(user.visa_category)))
      .finally(() => setReady(true));
  }, [user]);

  useEffect(() => {
    if (!ready) return;
    setLoading(true);
    getCreatorPosts(visaType, statusLabel)
      .then(setPosts)
      .finally(() => setLoading(false));
  }, [visaType, statusLabel, ready]);

  return (
    <div className="container">
      <div className="page-head row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>Creator feed</h1>
          <p>Fast, labeled updates from verified creators — matched to official sources.</p>
        </div>
        {isCreator && (
          <button className="btn pink" onClick={() => setShowModal(true)}>+ New post</button>
        )}
      </div>

      <FeedFilterBar
        visaType={visaType}
        statusLabel={statusLabel}
        onVisaChange={setVisaType}
        onStatusChange={setStatusLabel}
      />
      <Disclaimer />

      {loading ? (
        <>
          <div className="card skeleton" style={{ height: 120 }} />
          <div className="card skeleton" style={{ height: 120 }} />
        </>
      ) : posts.length === 0 ? (
        <div className="card">
          <p style={{ margin: 0 }}>No posts match your current filters.</p>
        </div>
      ) : (
        <div className="stack">
          {posts.map((p) => (
            <CreatorPostCard key={p.id} post={p} />
          ))}
        </div>
      )}

      {showModal && (
        <CreatePostModal
          onClose={() => setShowModal(false)}
          onCreated={(post) => setPosts((prev) => [post, ...prev])}
        />
      )}
    </div>
  );
}
