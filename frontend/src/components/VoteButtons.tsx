import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface Props {
  targetType: "post" | "answer";
  targetId: number;
  score: number;
}

export default function VoteButtons({ targetType, targetId, score }: Props) {
  const { user } = useAuth();
  const [current, setCurrent] = useState(score);
  const [busy, setBusy] = useState(false);

  async function vote(value: number) {
    if (!user || busy) return;
    setBusy(true);
    const prev = current;
    setCurrent((c) => c + value); // optimistic
    try {
      await api.post("/votes", {
        target_type: targetType,
        target_id: targetId,
        value,
      });
    } catch {
      setCurrent(prev); // revert on failure
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className="vote">
      <button onClick={() => vote(1)} title="Upvote" disabled={!user}>
        ▲
      </button>
      <strong>{current}</strong>
      <button onClick={() => vote(-1)} title="Downvote" disabled={!user}>
        ▼
      </button>
    </span>
  );
}
