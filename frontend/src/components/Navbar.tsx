"use client";

import { useState, useEffect } from "react";

const NAV_LINKS = [
  { label: "Today", href: "#today" },
  { label: "Search", href: "#search" },
  { label: "Trends", href: "#trends" },
  { label: "𝕏", href: "#tweets" },
  { label: "Research", href: "#research" },
  { label: "Videos", href: "#videos" },
  { label: "Feed", href: "#feed" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
      style={{
        background: scrolled
          ? "rgba(10, 10, 15, 0.85)"
          : "transparent",
        backdropFilter: scrolled ? "blur(20px)" : "none",
        borderBottom: scrolled ? "1px solid var(--color-border)" : "1px solid transparent",
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        {/* Logo */}
        <a href="#today" className="flex items-center gap-3 group">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-transform duration-300 group-hover:scale-110"
            style={{ background: "var(--gradient-hero)" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="2" x2="12" y2="6" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="2" y1="12" x2="6" y2="12" />
              <line x1="18" y1="12" x2="22" y2="12" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <span className="text-lg font-bold tracking-tight hidden sm:block" style={{ color: "var(--color-text)" }}>
            AI Intelligence Radar
          </span>
        </a>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105"
              style={{ color: "var(--color-text-muted)" }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "var(--color-text)";
                e.currentTarget.style.background = "var(--color-surface-2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--color-text-muted)";
                e.currentTarget.style.background = "transparent";
              }}
            >
              {link.label}
            </a>
          ))}
          {/* Live indicator */}
          <div className="ml-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full" style={{ background: "rgba(0,184,148,0.1)" }}>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: "var(--color-success)" }} />
              <span className="relative inline-flex rounded-full h-2 w-2" style={{ background: "var(--color-success)" }} />
            </span>
            <span className="text-xs font-semibold" style={{ color: "var(--color-success)" }}>Live</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
