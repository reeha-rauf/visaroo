/**
 * Visual theming per visa category — a CSS gradient "banner" + a line-icon key.
 * No external images and no emoji: every card/slide gets a full, intentional-looking
 * background from the olive / pink / brown palette, plus an SVG icon (see CategoryIcon).
 */
export type CategoryIconKey =
  | "gradcap"
  | "briefcase"
  | "flask"
  | "building"
  | "home"
  | "globe"
  | "plane"
  | "idcard"
  | "clipboard";

export interface CategoryTheme {
  gradient: string;
  icon: CategoryIconKey;
}

const THEMES: Record<string, CategoryTheme> = {
  "F-1": { gradient: "linear-gradient(135deg, #6b7a3f, #525e30)", icon: "gradcap" },
  OPT: { gradient: "linear-gradient(135deg, #8a6d4f, #6b7a3f)", icon: "briefcase" },
  "STEM-OPT": { gradient: "linear-gradient(135deg, #525e30, #8a6d4f)", icon: "flask" },
  "H-1B": { gradient: "linear-gradient(135deg, #e49bb0, #8a6d4f)", icon: "building" },
  "H-4": { gradient: "linear-gradient(135deg, #e49bb0, #6b7a3f)", icon: "home" },
  "J-1": { gradient: "linear-gradient(135deg, #6b7a3f, #e49bb0)", icon: "globe" },
  "L-1": { gradient: "linear-gradient(135deg, #8a6d4f, #525e30)", icon: "plane" },
  "Green-Card": { gradient: "linear-gradient(135deg, #6b7a3f, #8a6d4f)", icon: "idcard" },
  Other: { gradient: "linear-gradient(135deg, #857f72, #6b7a3f)", icon: "clipboard" },
};

export function categoryTheme(category: string): CategoryTheme {
  return THEMES[category] ?? THEMES.Other;
}
