import { useEffect, useState } from "react";
import { getProfile } from "../api/profile";
import {
  getWebinars,
  WEBINAR_VISA_TAGS,
  type Webinar,
} from "../api/webinars";
import Disclaimer from "../components/Disclaimer";
import FilterChips from "../components/FilterChips";
import WebinarCard from "../components/WebinarCard";
import { useAuth } from "../context/AuthContext";

// Map a profile visa_category (hyphen form) to a webinar tag (underscore form).
function toTag(visaCategory?: string | null): string {
  if (!visaCategory) return "ALL";
  const t = visaCategory.replace("-", "_"); // STEM-OPT -> STEM_OPT
  return (WEBINAR_VISA_TAGS as readonly string[]).includes(t) ? t : "ALL";
}

export default function WebinarsPage() {
  const { user } = useAuth();
  const [filter, setFilter] = useState<string>("ALL");
  const [filterReady, setFilterReady] = useState(false);
  const [showPast, setShowPast] = useState(false);
  const [webinars, setWebinars] = useState<Webinar[]>([]);
  const [loading, setLoading] = useState(true);

  // Default the filter to the user's visa type (from profile) on mount.
  useEffect(() => {
    if (!user) {
      setFilterReady(true);
      return;
    }
    getProfile()
      .then((p) => setFilter(toTag(p?.visaType ?? user.visa_category)))
      .catch(() => setFilter(toTag(user.visa_category)))
      .finally(() => setFilterReady(true));
  }, [user]);

  useEffect(() => {
    if (!filterReady) return;
    setLoading(true);
    getWebinars(filter, showPast)
      .then(setWebinars)
      .finally(() => setLoading(false));
  }, [filter, showPast, filterReady]);

  return (
    <div className="container">
      <div className="page-head">
        <h1>Webinars</h1>
        <p>Upcoming immigration webinars, in your local time.</p>
      </div>

      <FilterChips selected={filter} onChange={setFilter} availableTags={WEBINAR_VISA_TAGS} />
      <Disclaimer />

      {loading ? (
        <>
          <div className="card skeleton" style={{ height: 120 }} />
          <div className="card skeleton" style={{ height: 120 }} />
        </>
      ) : webinars.length === 0 ? (
        <div className="card">
          <p style={{ margin: 0 }}>
            No {showPast ? "" : "upcoming "}webinars for your status. Check back soon.
          </p>
        </div>
      ) : (
        <div className="stack">
          {webinars.map((w) => (
            <WebinarCard key={w.id} webinar={w} />
          ))}
        </div>
      )}

      <button
        className="btn ghost"
        style={{ marginTop: 12 }}
        onClick={() => setShowPast((s) => !s)}
      >
        {showPast ? "Hide past webinars" : "Show past webinars"}
      </button>
    </div>
  );
}
