"use client";

import { useTodayReport } from "@/hooks/useApi";

const SECTION_ICONS: Record<string, string> = {
  announcements: "📢",
  breakthroughs: "🔬",
  tools: "🛠️",
  discussions: "💬",
  insights: "🧠",
};

const SECTION_LABELS: Record<string, string> = {
  announcements: "Major Announcements",
  breakthroughs: "Research Breakthroughs",
  tools: "New AI Tools",
  discussions: "Trending Discussions",
  insights: "Strategic Insights",
};

const SECTION_COLORS: Record<string, string> = {
  announcements: "var(--color-accent-bright)",
  breakthroughs: "var(--color-accent-2)",
  tools: "var(--color-accent-3)",
  discussions: "var(--color-accent-4)",
  insights: "var(--color-accent-5)",
};

export function HeroReport() {
  const { report, loading, error } = useTodayReport();

  if (loading) {
    return (
      <div className="animate-fade-in">
        <div className="skeleton h-10 w-72 mb-4" />
        <div className="skeleton h-64 w-full rounded-2xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card text-center py-16 animate-fade-in">
        <div className="text-4xl mb-4">📡</div>
        <h2 className="text-xl font-bold mb-2" style={{ color: "var(--color-text)" }}>
          Connecting to Intelligence Network...
        </h2>
        <p style={{ color: "var(--color-text-muted)" }}>
          Backend is not reachable. Start the server with <code className="px-2 py-0.5 rounded" style={{ background: "var(--color-surface-2)" }}>docker compose up</code>
        </p>
      </div>
    );
  }

  const sections = report?.sections || {};

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-1 h-8 rounded-full" style={{ background: "var(--gradient-hero)" }} />
        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight" style={{ color: "var(--color-text)" }}>
          Today in AI
        </h1>
        <span className="badge badge-purple ml-2">{report?.date || "Today"}</span>
      </div>

      {/* Report title + summary */}
      <div className="card glow mb-8 mt-4" style={{ borderColor: "var(--color-accent)", borderWidth: "1px" }}>
        <h2
          className="text-xl sm:text-2xl font-bold mb-3"
          style={{
            background: "var(--gradient-hero)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          {report?.title || "AI Intelligence Report"}
        </h2>
        <p className="text-base leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
          {report?.summary || "Generating today's intelligence report..."}
        </p>
      </div>

      {/* Sections grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(sections).map(([key, items], idx) => {
          const sectionItems = items as Array<{ headline: string; detail: string; sources?: string[] }>;
          if (!sectionItems || sectionItems.length === 0) return null;

          return (
            <div
              key={key}
              className={`card animate-fade-in animate-fade-in-delay-${idx + 1}`}
              style={{ borderTop: `2px solid ${SECTION_COLORS[key] || "var(--color-border)"}` }}
            >
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">{SECTION_ICONS[key] || "📌"}</span>
                <h3 className="text-sm font-bold uppercase tracking-wider" style={{ color: SECTION_COLORS[key] || "var(--color-text)" }}>
                  {SECTION_LABELS[key] || key}
                </h3>
              </div>
              <ul className="space-y-3">
                {sectionItems.slice(0, 4).map((item, i) => (
                  <li key={i}>
                    <p className="text-sm font-semibold mb-0.5" style={{ color: "var(--color-text)" }}>
                      {item.headline}
                    </p>
                    <p className="text-xs leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
                      {item.detail}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
