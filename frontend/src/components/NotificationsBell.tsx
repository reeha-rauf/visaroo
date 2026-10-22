import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getNotifications,
  getUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
  type AppNotification,
  type NotificationType,
} from "../api/notifications";
import { ChatIcon, StarIcon, UpvoteIcon } from "./icons";

function NotifIcon({ type }: { type: NotificationType }) {
  switch (type) {
    case "new_answer":
      return <ChatIcon size={16} />;
    case "best_answer":
      return <StarIcon size={16} />;
    case "post_upvote":
    case "answer_upvote":
      return <UpvoteIcon size={16} />;
    default:
      return <ChatIcon size={16} />;
  }
}

const POLL_MS = 60_000;

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.round(hrs / 24)}d ago`;
}

/** Nav bell with an unread badge and a dropdown of recent activity on your content. */
export default function NotificationsBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  const refreshCount = useCallback(() => {
    getUnreadCount().then(setUnread).catch(() => {});
  }, []);

  // Poll the unread count in the background.
  useEffect(() => {
    refreshCount();
    const id = window.setInterval(refreshCount, POLL_MS);
    return () => window.clearInterval(id);
  }, [refreshCount]);

  // Load the full list when the dropdown opens.
  useEffect(() => {
    if (!open) return;
    getNotifications().then(setItems).catch(() => setItems([]));
  }, [open]);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  async function openNotification(n: AppNotification) {
    setOpen(false);
    if (!n.read) {
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      setUnread((u) => Math.max(0, u - 1));
      markNotificationRead(n.id).catch(() => {});
    }
    if (n.postId) navigate(`/posts/${n.postId}`);
  }

  async function markAll() {
    setItems((prev) => prev.map((x) => ({ ...x, read: true })));
    setUnread(0);
    await markAllNotificationsRead().catch(() => {});
  }

  return (
    <div className="notif-menu" ref={ref}>
      <button
        className="notif-trigger"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`}
        title="Notifications"
      >
        <svg
          className="notif-bell-icon"
          width="19"
          height="19"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unread > 0 && <span className="notif-badge">{unread > 9 ? "9+" : unread}</span>}
      </button>

      {open && (
        <div className="notif-dropdown" role="menu">
          <div className="notif-head">
            <strong>Notifications</strong>
            {items.some((n) => !n.read) && (
              <button className="notif-markall" onClick={markAll}>
                Mark all read
              </button>
            )}
          </div>

          {items.length === 0 ? (
            <p className="muted notif-empty">
              No notifications yet. When someone answers or upvotes your posts, you’ll
              see it here.
            </p>
          ) : (
            <div className="notif-list">
              {items.map((n) => (
                <button
                  key={n.id}
                  className={`notif-item ${n.read ? "" : "unread"}`}
                  onClick={() => openNotification(n)}
                  role="menuitem"
                >
                  <span className="notif-icon"><NotifIcon type={n.type} /></span>
                  <span className="notif-text">
                    <span className="notif-msg">
                      <strong>{n.actor}</strong> {n.message}
                    </span>
                    <span className="muted notif-time">{timeAgo(n.createdAt)}</span>
                  </span>
                  {!n.read && <span className="notif-dot" aria-hidden />}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
