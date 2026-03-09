"use client";

import { useContent } from "@/hooks/useApi";

export function ResearchPapers() {
  const { items, loading, error } = useContent("paper", 12);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 rounded-full" style={{ background: "var(--color-accent-2)" }} />
        <h2 className="text-2xl font-extrabold tracking-tight">Research Papers</h2>
        <span className="badge badge-teal">arXiv</span>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton h-32 rounded-2xl" />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-8">
          <p style={{ color: "var(--color-text-muted)" }}>Unable to load research papers.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-3">📄</div>
          <p className="font-semibold mb-1">No Papers Yet</p>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            Papers from arXiv (cs.AI, cs.CL, cs.LG) will appear here after ingestion.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((paper, idx) => {
            const categories = (paper.metadata?.categories as string[]) || [];
            return (
              <a
                key={paper.id}
                href={paper.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className={`card group cursor-pointer animate-fade-in animate-fade-in-delay-${Math.min(idx + 1, 4)}`}
                style={{ borderLeft: "3px solid var(--color-accent-2)" }}
              >
                <h4 className="text-sm font-semibold mb-2 group-hover:underline leading-snug" style={{ color: "var(--color-text)" }}>
                  {paper.title}
                </h4>

                <p className="text-xs line-clamp-3 mb-3" style={{ color: "var(--color-text-muted)" }}>
                  {paper.body.slice(0, 250)}
                </p>

                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-medium" style={{ color: "var(--color-text-dim)" }}>
                    {paper.author?.slice(0, 60)}
                  </span>
                  <div className="flex gap-1">
                    {categories.slice(0, 3).map((cat) => (
                      <span key={cat} className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: "var(--color-surface-2)", color: "var(--color-accent-2)" }}>
                        {cat}
                      </span>
                    ))}
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}
