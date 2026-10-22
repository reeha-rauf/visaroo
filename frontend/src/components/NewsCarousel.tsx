import { useEffect, useMemo, useRef, useState } from "react";
import type { NewsItem } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { categoryTheme } from "../lib/categoryTheme";
import { CategoryIcon } from "./icons";

const AUTOPLAY_MS = 5500;

/**
 * Pick the most relevant items for the carousel: only items tagged to a real visa
 * category (we drop "Other", which is where the broad/unclassified feed lands), and
 * surface the logged-in user's own category first. Falls back to the raw list only if
 * nothing has a real category, so the carousel is never empty.
 */
function relevantSlides(items: NewsItem[], userCategory?: string): NewsItem[] {
  const real = items.filter((n) => n.visa_category && n.visa_category !== "Other");
  const pool = real.length > 0 ? real : items;
  if (!userCategory) return pool.slice(0, 6);
  const mine = pool.filter((n) => n.visa_category === userCategory);
  const rest = pool.filter((n) => n.visa_category !== userCategory);
  return [...mine, ...rest].slice(0, 6);
}

export default function NewsCarousel({ items }: { items: NewsItem[] }) {
  const { user } = useAuth();
  const [index, setIndex] = useState(0);
  const timer = useRef<number | null>(null);
  const slides = useMemo(
    () => relevantSlides(items, user?.visa_category),
    [items, user?.visa_category],
  );

  function go(next: number) {
    setIndex((next + slides.length) % slides.length);
  }

  // Autoplay, paused on hover (handled via start/stop below).
  function start() {
    stop();
    timer.current = window.setInterval(() => {
      setIndex((i) => (i + 1) % slides.length);
    }, AUTOPLAY_MS);
  }
  function stop() {
    if (timer.current) {
      window.clearInterval(timer.current);
      timer.current = null;
    }
  }

  useEffect(() => {
    if (slides.length > 1) start();
    return stop;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slides.length]);

  if (slides.length === 0) return null;

  // Clamp in case `slides` shrank after items/user changed but `index` is stale.
  const safeIndex = index % slides.length;

  return (
    <div>
      <div
        className="carousel"
        onMouseEnter={stop}
        onMouseLeave={start}
      >
        <div
          className="carousel-track"
          style={{ transform: `translateX(-${safeIndex * 100}%)` }}
        >
          {slides.map((n) => {
            const theme = categoryTheme(n.visa_category);
            const bg = n.image_url
              ? `center / cover no-repeat url("${n.image_url}")`
              : theme.gradient;
            return (
              <div
                className="slide"
                key={n.id}
                style={{ background: bg }}
              >
                <div className="overlay" />
                {!n.image_url && (
                  <span className="slide-icon"><CategoryIcon icon={theme.icon} size={48} /></span>
                )}
                <div className="slide-content">
                  <span className="tag">{n.visa_category}</span>
                  <h3>{n.title}</h3>
                  <p>{n.summary}</p>
                  <a
                    href={n.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: "#fff", fontWeight: 700 }}
                  >
                    Read the full source →
                  </a>
                </div>
              </div>
            );
          })}
        </div>

        {slides.length > 1 && (
          <>
            <button
              className="carousel-arrow left"
              onClick={() => go(index - 1)}
              aria-label="Previous"
            >
              ‹
            </button>
            <button
              className="carousel-arrow right"
              onClick={() => go(index + 1)}
              aria-label="Next"
            >
              ›
            </button>
          </>
        )}
      </div>

      {slides.length > 1 && (
        <div className="carousel-dots">
          {slides.map((_, i) => (
            <button
              key={i}
              className={i === safeIndex ? "active" : ""}
              onClick={() => go(i)}
              aria-label={`Go to slide ${i + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
