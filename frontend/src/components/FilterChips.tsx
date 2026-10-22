interface Props {
  selected: string;
  onChange: (tag: string) => void;
  availableTags: readonly string[];
}

/** Single-select visa-type filter chips. "ALL" is just another single selection. */
export default function FilterChips({ selected, onChange, availableTags }: Props) {
  return (
    <div className="row" style={{ flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
      {availableTags.map((tag) => (
        <button
          key={tag}
          type="button"
          className={selected === tag ? "chip-btn active" : "chip-btn"}
          onClick={() => onChange(tag)}
        >
          {tag === "ALL" ? "All" : tag.replace("_", " ")}
        </button>
      ))}
    </div>
  );
}
