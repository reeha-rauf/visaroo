import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { DocIcon, GearIcon, LogoutIcon } from "./icons";
import NotificationsBell from "./NotificationsBell";

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    if (q.trim().length < 2) return;
    navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  }

  // Close the account menu on outside click or Escape.
  useEffect(() => {
    if (!menuOpen) return;
    function onDocClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  function handleLogout() {
    setMenuOpen(false);
    logout();
    navigate("/");
  }

  return (
    <nav className="nav">
      <Link to="/" className="logo">
        <span className="roo">🦘</span> Visaroo
      </Link>

      {user && (
        <div className="links">
          <Link to="/">Community</Link>
          <Link to="/feed">Feed</Link>
          <Link to="/news">News</Link>
          <Link to="/webinars">Webinars</Link>
          <Link to="/legal-help">Legal help</Link>
        </div>
      )}

      <div className="spacer" />

      {user && (
        <form className="nav-search" onSubmit={submitSearch}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search Visaroo…"
            aria-label="Search Visaroo"
          />
        </form>
      )}

      {user ? (
        <div className="links">
          <Link to="/new" className="btn pink">+ Post</Link>
          <Link to="/deadlines">Deadlines</Link>
          <NotificationsBell />
          <div className="account-menu" ref={menuRef}>
            <button
              className="account-trigger"
              onClick={() => setMenuOpen((o) => !o)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <span className="account-avatar">{user.username.charAt(0).toUpperCase()}</span>
              <span className="account-name">{user.username}</span>
              <span className="account-caret">▾</span>
            </button>
            {menuOpen && (
              <div className="account-dropdown" role="menu">
                <Link
                  to="/my-posts"
                  role="menuitem"
                  className="account-item"
                  onClick={() => setMenuOpen(false)}
                >
                  <DocIcon /> My posts
                </Link>
                <Link
                  to="/profile"
                  role="menuitem"
                  className="account-item"
                  onClick={() => setMenuOpen(false)}
                >
                  <GearIcon /> Profile settings
                </Link>
                <button
                  role="menuitem"
                  className="account-item danger"
                  onClick={handleLogout}
                >
                  <LogoutIcon /> Log out
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="links">
          <Link to="/login" className="btn ghost">Log in</Link>
          <Link to="/signup" className="btn">Sign up</Link>
        </div>
      )}
    </nav>
  );
}
