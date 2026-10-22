import {
  CATEGORY_TITLES,
  LEGAL_RESOURCES,
  type ResourceCategory,
} from "../data/legalResources";

const ORDER: ResourceCategory[] = ["attorney", "free_help", "university", "government"];

/** Curated legal resources grouped by category (spec REQ-5 / TASK-6). */
export default function ResourceDirectory() {
  return (
    <div>
      <h2 style={{ color: "var(--olive-dark)" }}>Legal resources</h2>
      {ORDER.map((cat) => {
        const items = LEGAL_RESOURCES.filter((r) => r.category === cat);
        if (!items.length) return null;
        return (
          <div key={cat} style={{ marginBottom: 20 }}>
            <h3 style={{ color: "var(--olive-dark)", marginBottom: 10 }}>
              {CATEGORY_TITLES[cat]}
            </h3>
            <div className="stack">
              {items.map((r) => (
                <div className="card" key={r.name} style={{ marginBottom: 10 }}>
                  <div className="row" style={{ justifyContent: "space-between", gap: 8 }}>
                    <strong>{r.name}</strong>
                    {r.region && <span className="tag">{r.region}</span>}
                  </div>
                  <p className="muted" style={{ margin: "6px 0 10px" }}>{r.description}</p>
                  <a
                    className="btn secondary"
                    href={r.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Visit →
                  </a>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
