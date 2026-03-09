"use client";

import { useContent } from "@/hooks/useApi";

const TYPE_CONFIG: Record<string, { icon: string; class: string; label: string }> = {
  tweet: { icon: "𝕏", class: "type-tweet", label: "Tweet" },
  video: { icon: "▶", class: "type-video", label: "Video" },
  article: { icon: "📰", class: "type-article", label: "Article" },
  paper: { icon: "📄", class: "type-paper", label: "Paper" },
  repo: { icon: "⚡", class: "type-repo", label: "Repo" },
};

function formatEngagement(eng: Record<string, number>): string {
  const parts: string[] = [];
  if (eng.likes) parts.push(`♥ ${eng.likes.toLocaleString()}`);
  if (eng.views) parts.push(`👁 ${eng.views.toLocaleString()}`);
  if (eng.stars) parts.push(`⭐ ${eng.stars.toLocaleString()}`);
  if (eng.retweets) parts.push(`🔄 ${eng.retweets.toLocaleString()}`);
  if (eng.forks) parts.push(`🍴 ${eng.forks.toLocaleString()}`);
  if (eng.comments) parts.push(`💬 ${eng.comments.toLocaleString()}`);
  return parts.join("  ") || "";
}

export function ContentFeed() {
  const { items, loading, error } = useContent(undefined, 30);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 rounded-full" style={{ background: "var(--color-accent-4)" }} />
        <h2 className="text-2xl font-extrabold tracking-tight">Latest Feed</h2>
        <span className="badge badge-gold">{items.length} items</span>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton h-24 rounded-2xl" />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-8">
          <p style={{ color: "var(--color-text-muted)" }}>Unable to load content feed.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-3">📡</div>
          <p className="font-semibold mb-1">No Content Yet</p>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            Run the content ingestion worker to start collecting data from all sources.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => {
            const cfg = TYPE_CONFIG[item.content_type] || { icon: "📌", class: "", label: item.content_type };
            const engText = formatEngagement(item.engagement);
            return (
              <a
                key={item.id}
                href={item.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="card block group cursor-pointer"
                style={{ padding: "1rem 1.25rem" }}
              >
                <div className="flex items-start gap-3">
                  {/* Type icon */}
                  <span className={`text-xl flex-shrink-0 mt-0.5 ${cfg.class}`}>{cfg.icon}</span>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] uppercase font-bold tracking-wider" style={{ color: "var(--color-text-dim)" }}>
                        {cfg.label}
                      </span>
                      <span className="text-[10px]" style={{ color: "var(--color-text-dim)" }}>•</span>
                      <span className="text-[10px]" style={{ color: "var(--color-text-dim)" }}>
                        {item.source}
                      </span>
                      {item.published_at && (
                        <>
                          <span className="text-[10px]" style={{ color: "var(--color-text-dim)" }}>•</span>
                          <span className="text-[10px]" style={{ color: "var(--color-text-dim)" }}>
                            {new Date(item.published_at).toLocaleDateString()}
                          </span>
                        </>
                      )}
                    </div>

                    <h4 className="text-sm font-semibold mb-1 group-hover:underline" style={{ color: "var(--color-text)" }}>
                      {item.title || item.body.slice(0, 100)}
                    </h4>

                    {item.title && (
                      <p className="text-xs line-clamp-2" style={{ color: "var(--color-text-muted)" }}>
                        {item.body.slice(0, 200)}
                      </p>
                    )}

                    {engText && (
                      <p className="text-[10px] mt-1.5 font-medium" style={{ color: "var(--color-text-dim)" }}>
                        {engText}
                      </p>
                    )}
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
