import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getProfile, type ProfileOut } from "../api/profile";
import CaseBriefSection from "../components/CaseBriefSection";
import DisclaimerBanner from "../components/DisclaimerBanner";
import ResourceDirectory from "../components/ResourceDirectory";
import { computeDeadlines } from "../utils/computeDeadlines";

export default function AttorneyHelpPage() {
  const [params] = useSearchParams();
  const prefill = params.get("prefill") === "true";
  const [profile, setProfile] = useState<ProfileOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .finally(() => setLoading(false));
  }, []);

  // Deadlines computed client-side (no API) from the loaded profile.
  const deadlines = useMemo(
    () => (profile ? computeDeadlines(profile, new Date()) : []),
    [profile],
  );

  return (
    <div className="container">
      <div className="page-head">
        <h1>Legal help</h1>
        <p>Prepare for a conversation with an attorney or your DSO.</p>
      </div>

      <DisclaimerBanner />

      {loading ? (
        <div className="card skeleton" style={{ height: 160 }} />
      ) : profile ? (
        <CaseBriefSection profile={profile} deadlines={deadlines} prefill={prefill} />
      ) : (
        <div className="card">
          <p style={{ margin: 0 }}>
            Set up your profile to generate a personalized case brief — the resources
            below are available to everyone.
          </p>
        </div>
      )}

      <ResourceDirectory />
    </div>
  );
}
