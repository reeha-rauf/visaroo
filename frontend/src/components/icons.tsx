/**
 * Small line-style icon set (stroke, currentColor) used across the app.
 * No emoji — consistent with the notifications bell.
 */
import type { CategoryIconKey } from "../lib/categoryTheme";

interface IconProps {
  size?: number;
  className?: string;
}

function base(size: number, className?: string) {
  return {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    className,
  };
}

/** Document with a pencil — "My posts". */
export function DocIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <path d="M8 8h5" />
      <path d="M8 12h4" />
      <path d="M17.5 3.5a1.8 1.8 0 0 1 2.5 2.5L15 11l-3 1 1-3Z" />
    </svg>
  );
}

/** Gear — "Profile settings". */
export function GearIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z" />
    </svg>
  );
}

/** Logout — door with arrow. */
export function LogoutIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  );
}

/* ---------------------------- Functional ---------------------------- */

/** Map pin — "Pin countdown". */
export function PinIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M12 21s-6-5.5-6-10a6 6 0 0 1 12 0c0 4.5-6 10-6 10Z" />
      <circle cx="12" cy="11" r="2.5" />
    </svg>
  );
}

/** Download arrow into tray. */
export function DownloadIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="M7 10l5 5 5-5" />
      <path d="M12 15V3" />
    </svg>
  );
}

/** Circular refresh arrows. */
export function RefreshIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M21 12a9 9 0 1 1-2.64-6.36" />
      <path d="M21 3v4.5H16.5" />
    </svg>
  );
}

/** Close X. */
export function CloseIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

/** Pencil — edit / override. */
export function EditIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}

/** Triangle warning. */
export function WarningIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

/** Search magnifier. */
export function SearchIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

/** Clock — countdown timer. */
export function ClockIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

/** Chevron left — collapse/minimize. */
export function ChevronLeftIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="m15 18-6-6 6-6" />
    </svg>
  );
}

/** Scales of justice — legal help. */
export function ScaleIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M12 3v18" />
      <path d="M7 7h10" />
      <path d="M7 7 4 13h6L7 7Z" />
      <path d="M17 7l-3 6h6l-3-6Z" />
      <path d="M8 21h8" />
      <path d="M4 13a3 3 0 0 0 6 0" />
      <path d="M14 13a3 3 0 0 0 6 0" />
    </svg>
  );
}

/* ----------------------- Landing feature icons ---------------------- */

/** Speech bubbles — community Q&A. */
export function ChatIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 9.5 9.5 0 0 1-4-.9L3 21l1-4a8.4 8.4 0 0 1-1-4.1 8.5 8.5 0 0 1 9-8.4 8.4 8.4 0 0 1 9 7Z" />
    </svg>
  );
}

/** Shield — AI gatekeeper. */
export function ShieldIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
    </svg>
  );
}

/** Newspaper — personalized news. */
export function NewspaperIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M4 22a2 2 0 0 1-2-2V4a1 1 0 0 1 1-1h13a1 1 0 0 1 1 1v16a2 2 0 0 0 2 2H4Z" />
      <path d="M18 7h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2" />
      <path d="M6 7h8" />
      <path d="M6 11h8" />
      <path d="M6 15h5" />
    </svg>
  );
}

/** Up arrow — upvote notification. */
export function UpvoteIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M12 19V5" />
      <path d="m5 12 7-7 7 7" />
    </svg>
  );
}

/** Star — best-answer notification. */
export function StarIcon({ size = 16, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8L3.5 9.7l5.9-.9L12 3.5Z" />
    </svg>
  );
}

/* ---------------------- Visa category icons ------------------------- */
// Distinct line icon per visa category (used on post cards + news carousel).

/** Graduation cap — F-1. */
export function GradCapIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M22 10 12 5 2 10l10 5 10-5Z" />
      <path d="M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5" />
      <path d="M22 10v5" />
    </svg>
  );
}

/** Briefcase — OPT. */
export function BriefcaseIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <rect x="2" y="7" width="20" height="14" rx="2" />
      <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2" />
      <path d="M2 13h20" />
    </svg>
  );
}

/** Flask — STEM-OPT. */
export function FlaskIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M9 3h6" />
      <path d="M10 3v6l-5.2 8.3A2 2 0 0 0 6.5 21h11a2 2 0 0 0 1.7-3.7L14 9V3" />
      <path d="M7.5 15h9" />
    </svg>
  );
}

/** Office building — H-1B. */
export function BuildingIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <rect x="5" y="3" width="14" height="18" rx="1" />
      <path d="M9 7h2M13 7h2M9 11h2M13 11h2M9 15h2M13 15h2" />
      <path d="M10 21v-3h4v3" />
    </svg>
  );
}

/** House — H-4. */
export function HomeIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5" />
      <path d="M9.5 21v-6h5v6" />
    </svg>
  );
}

/** Globe — J-1. */
export function GlobeIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z" />
    </svg>
  );
}

/** Plane — L-1. */
export function PlaneIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <path d="M17.8 19.8 16 14l-3.5 3.5V21l-2-2-2 2v-3.5L5 14l-1.8 5.8" />
      <path d="M22 5.5a2 2 0 0 0-2.8-2.8L3 11l5 1.5L19.2 3.2" />
    </svg>
  );
}

/** ID card — Green-Card. */
export function IdCardIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <circle cx="8" cy="11" r="2" />
      <path d="M5 16c.6-1.5 1.8-2.3 3-2.3s2.4.8 3 2.3" />
      <path d="M14 10h5M14 13h5" />
    </svg>
  );
}

/** Clipboard — Other / default. */
export function ClipboardIcon({ size = 20, className }: IconProps) {
  return (
    <svg {...base(size, className)}>
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2" />
      <path d="M9 11h6M9 15h4" />
    </svg>
  );
}

/** Render the line icon for a visa category by its theme key. */
export function CategoryIcon({
  icon,
  size = 26,
  className,
}: { icon: CategoryIconKey } & IconProps) {
  switch (icon) {
    case "gradcap":
      return <GradCapIcon size={size} className={className} />;
    case "briefcase":
      return <BriefcaseIcon size={size} className={className} />;
    case "flask":
      return <FlaskIcon size={size} className={className} />;
    case "building":
      return <BuildingIcon size={size} className={className} />;
    case "home":
      return <HomeIcon size={size} className={className} />;
    case "globe":
      return <GlobeIcon size={size} className={className} />;
    case "plane":
      return <PlaneIcon size={size} className={className} />;
    case "idcard":
      return <IdCardIcon size={size} className={className} />;
    case "clipboard":
    default:
      return <ClipboardIcon size={size} className={className} />;
  }
}
