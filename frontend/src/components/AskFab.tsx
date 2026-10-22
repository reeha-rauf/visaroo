import { useAsk } from "../context/AskContext";

/** Floating "Ask Visaroo" action button, bottom-right, chatbot-style. */
export default function AskFab() {
  const { open, openPanel } = useAsk();

  // Hide the FAB while the panel is open so they don't overlap.
  if (open) return null;

  return (
    <button
      className="ask-fab"
      onClick={() => openPanel()}
      aria-label="Ask Visaroo"
      title="Ask Visaroo"
    >
      <span className="ask-fab-icon">🦘</span>
      <span className="ask-fab-label">Ask</span>
    </button>
  );
}
