import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  askImpact,
  STATUS_DISPLAY,
  type AskResponse,
  type AskTurn,
} from "../api/ask";
import { useAsk } from "../context/AskContext";
import { useAuth } from "../context/AuthContext";
import { CloseIcon } from "./icons";

export default function AskPanel() {
  const { open, prefill, closePanel } = useAsk();
  const { user } = useAuth();
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<AskTurn[]>([]);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Apply prefill + focus when the panel opens.
  useEffect(() => {
    if (open) {
      if (prefill) setQuestion(prefill);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open, prefill]);

  // Close on Escape.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && closePanel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closePanel]);

  async function submit() {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    try {
      const res = await askImpact(q, history);
      // Keep up to 3 turns of history for follow-ups.
      setHistory((h) => [...h, { question: q, answer: res.answer }].slice(-3));
      setResult(res);
      setQuestion("");
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  const status = result ? STATUS_DISPLAY[result.statusLabel] ?? STATUS_DISPLAY.UNCLEAR : null;

  return (
    <>
      <div className="ask-overlay" onClick={closePanel} />
      <aside className="ask-panel" role="dialog" aria-label="Ask Visaroo">
        <div className="ask-head">
          <h3>🦘 Ask Visaroo</h3>
          <button className="btn ghost" onClick={closePanel} aria-label="Close"><CloseIcon size={16} /></button>
        </div>

        {!user && (
          <div className="warn" style={{ margin: "0 0 12px" }}>
            <Link to="/login">Sign in</Link> for answers personalized to your visa status.
          </div>
        )}

        <div className="ask-body">
          {result && (
            <div className="ask-answer">
              {status && <span className={`status-chip ${status.tone}`}>{status.text}</span>}
              <p style={{ whiteSpace: "pre-wrap", marginTop: 10 }}>{result.answer}</p>

              {result.citations.length > 0 && (
                <div className="ask-citations">
                  <h4>Sources</h4>
                  {result.citations.map((c) => (
                    <div key={c.n} className="ask-citation">
                      <strong>[{c.n}] {c.title}</strong>
                      <div className="muted">
                        {c.source}
                        {c.url && (
                          <> · <a href={c.url} target="_blank" rel="noopener noreferrer">link</a></>
                        )}
                      </div>
                      <p className="muted ask-excerpt">"{c.excerpt}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="ask-input">
          <label>
            {result ? "Ask a follow-up" : "Ask about a rule or your status"} ({question.length}/500)
          </label>
          <textarea
            ref={inputRef}
            value={question}
            maxLength={500}
            disabled={loading}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="e.g. Does the new STEM OPT reporting rule affect me?"
          />
          <button className="btn" onClick={submit} disabled={loading || !question.trim()}>
            {loading ? "Thinking…" : "Ask"}
          </button>
        </div>
      </aside>
    </>
  );
}
