import { useEffect, useState } from "react";
import { api } from "./client";

// Canonical visa categories, fetched from the backend (falls back to a static list).
const FALLBACK = [
  "F-1", "OPT", "STEM-OPT", "H-1B", "H-4", "J-1", "L-1", "Green-Card", "Other",
];

export function useCategories(): string[] {
  const [categories, setCategories] = useState<string[]>(FALLBACK);
  useEffect(() => {
    api
      .get<{ categories: string[] }>("/meta/categories")
      .then((r) => setCategories(r.data.categories))
      .catch(() => setCategories(FALLBACK));
  }, []);
  return categories;
}
