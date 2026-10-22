import { Link } from "react-router-dom";
import type { ComponentType } from "react";
import {
  ChatIcon,
  NewspaperIcon,
  SearchIcon,
  ShieldIcon,
  WarningIcon,
} from "../components/icons";

const FEATURES: { Icon: ComponentType<{ size?: number }>; title: string; body: string }[] = [
  {
    Icon: ChatIcon,
    title: "Community Q&A",
    body: "Ask real questions and hear from people who've navigated the same visa path — post with your name or anonymously.",
  },
  {
    Icon: ShieldIcon,
    title: "AI gatekeeper",
    body: "Every post is gently checked for relevance and auto-tagged, so the community stays useful — never silenced.",
  },
  {
    Icon: SearchIcon,
    title: "Summary-first search",
    body: "Ask a question and get an AI summary of what the community said first, then the posts behind it.",
  },
  {
    Icon: NewspaperIcon,
    title: "Personalized news",
    body: "Official immigration updates, summarized in plain language and sorted to your visa category first.",
  },
];

const STEPS = [
  { num: "1", title: "Create your profile", body: "Tell us your visa category — F-1, OPT, H-1B, and more." },
  { num: "2", title: "Ask or search", body: "Get grounded answers from real lived experience." },
  { num: "3", title: "Stay ahead", body: "Follow the news that actually affects your status." },
];

export default function Landing() {
  return (
    <div className="container wide">
      <section className="hero">
        <span className="roo-big">🦘</span>
        <span className="kicker">For international students & visa holders</span>
        <h1>
          Navigate your visa journey, <span className="accent">together</span>.
        </h1>
        <p className="sub">
          Visaroo brings official immigration news and real community experience into one
          place — with AI that keeps answers relevant, grounded, and easy to find.
        </p>
        <div className="cta-row">
          <Link to="/signup" className="btn lg">Get started — it's free</Link>
          <Link to="/login" className="btn secondary lg">Log in</Link>
        </div>
      </section>

      <section className="features">
        {FEATURES.map((f) => (
          <div className="feature" key={f.title}>
            <div className="icon"><f.Icon size={26} /></div>
            <h3>{f.title}</h3>
            <p>{f.body}</p>
          </div>
        ))}
      </section>

      <h2 className="section-title">How Visaroo works</h2>
      <p className="section-sub">From uncertainty to clarity in three steps.</p>
      <section className="steps">
        {STEPS.map((s) => (
          <div className="step" key={s.num}>
            <div className="num">{s.num}</div>
            <h3 style={{ margin: "0 0 6px", color: "var(--olive-dark)" }}>{s.title}</h3>
            <p className="muted" style={{ margin: 0 }}>{s.body}</p>
          </div>
        ))}
      </section>

      <div className="disclaimer" style={{ maxWidth: 620, margin: "40px auto 0" }}>
        <WarningIcon size={16} /> Visaroo shares general information and community
        experiences — <strong>not legal advice</strong>. Always verify with your DSO or an
        immigration attorney.
      </div>

      <footer className="landing-footer">
        🦘 Visaroo · built for international students, by one.
      </footer>
    </div>
  );
}
