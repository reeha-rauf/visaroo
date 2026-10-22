import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import type { ProfileOut } from "../api/profile";
import type { ComputedDeadline } from "../utils/computeDeadlines";
import {
  briefToPlainText,
  generateBrief,
  type CaseBrief,
} from "../utils/generateBrief";

interface Props {
  profile: ProfileOut;
  deadlines: ComputedDeadline[];
  prefill: boolean;
}

export default function CaseBriefSection({ profile, deadlines, prefill }: Props) {
  const [description, setDescription] = useState("");
  const [brief, setBrief] = useState<CaseBrief | null>(null);
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ?prefill=true → focus the situation field on mount (spec REQ-1 / TASK-5).
  useEffect(() => {
    if (prefill) textareaRef.current?.focus();
  }, [prefill]);

  function handleGenerate() {
    setBrief(generateBrief({ profile, computedDeadlines: deadlines, situationDescription: description }));
    setCopied(false);
  }

  function plainText(): string {
    return brief ? briefToPlainText(brief) : "";
  }

  async function copy() {
    await navigator.clipboard.writeText(plainText());
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  function download() {
    const blob = new Blob([plainText()], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `visaroo-brief-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function mailtoDso(): string {
    const subject = encodeURIComponent(`Immigration question — ${profile.visaType}`);
    const body = encodeURIComponent(plainText());
    return `mailto:${profile.dsoEmail}?subject=${subject}&body=${body}`;
  }

  return (
    <div className="card">
      <h2 style={{ color: "var(--olive-dark)", marginTop: 0 }}>Your case brief</h2>
      <p className="muted" style={{ marginTop: 0 }}>
        Generate a concise summary of your status to bring to an attorney or your DSO.
        It's built on your device from your profile — nothing is sent to a server.
      </p>

      <label>Describe your situation (optional, {description.length}/500)</label>
      <textarea
        ref={textareaRef}
        value={description}
        maxLength={500}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="e.g. I changed employers last month and my STEM OPT extension is still pending."
      />

      <button className="btn" onClick={handleGenerate}>Generate my case brief</button>

      {brief && (
        <div style={{ marginTop: 18 }}>
          <pre className="brief-output">{plainText()}</pre>
          <div className="row" style={{ gap: 10, flexWrap: "wrap", marginTop: 10 }}>
            <button className="btn secondary" onClick={copy}>
              {copied ? "Copied!" : "Copy"}
            </button>
            <button className="btn secondary" onClick={download}>Download .txt</button>
            {profile.dsoEmail ? (
              <a className="btn" href={mailtoDso()}>Contact my DSO</a>
            ) : (
              <Link className="btn ghost" to="/profile">Add your DSO in profile settings →</Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
