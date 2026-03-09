"use client";

import { useContent } from "@/hooks/useApi";

function formatViews(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export function TopVideos() {
  const { items, loading, error } = useContent("video", 8);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 rounded-full" style={{ background: "#ff0000" }} />
        <h2 className="text-2xl font-extrabold tracking-tight">Top AI Videos</h2>
        <span className="badge" style={{ background: "rgba(255,0,0,0.1)", color: "#ff4444" }}>YouTube</span>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="skeleton h-48 rounded-2xl" />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-8">
          <p style={{ color: "var(--color-text-muted)" }}>Unable to load videos.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-3">🎬</div>
          <p className="font-semibold mb-1">No Videos Yet</p>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            AI videos from YouTube will appear here after the ingestion worker runs.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {items.map((video) => {
            const views = video.engagement?.views || 0;
            const likes = video.engagement?.likes || 0;
            const vid = video.url?.includes("v=") ? video.url.split("v=")[1] : "";
            const thumbUrl = vid
              ? `https://img.youtube.com/vi/${vid}/mqdefault.jpg`
              : null;

            return (
              <a
                key={video.id}
                href={video.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="card group cursor-pointer overflow-hidden"
                style={{ padding: 0 }}
              >
                {/* Thumbnail */}
                <div className="relative h-32 overflow-hidden bg-[var(--color-surface-2)]">
                  {thumbUrl ? (
                    <img
                      src={thumbUrl}
                      alt={video.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-3xl">▶</div>
                  )}
                  {/* Play overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ background: "rgba(0,0,0,0.4)" }}>
                    <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: "rgba(255,0,0,0.9)" }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                        <polygon points="5,3 19,12 5,21" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div className="p-3">
                  <h4 className="text-xs font-semibold mb-1.5 line-clamp-2 leading-snug group-hover:underline" style={{ color: "var(--color-text)" }}>
                    {video.title}
                  </h4>

                  <p className="text-[10px] mb-1.5" style={{ color: "var(--color-text-dim)" }}>
                    {video.author}
                  </p>

                  <div className="flex items-center gap-2 text-[10px]" style={{ color: "var(--color-text-dim)" }}>
                    {views > 0 && <span>👁 {formatViews(views)}</span>}
                    {likes > 0 && <span>♥ {formatViews(likes)}</span>}
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
