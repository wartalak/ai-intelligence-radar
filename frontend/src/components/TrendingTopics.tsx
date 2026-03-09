"use client";

import { useTrends } from "@/hooks/useApi";

export function TrendingTopics() {
  const { trends, loading, error } = useTrends();

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 rounded-full" style={{ background: "var(--color-accent-3)" }} />
        <h2 className="text-2xl font-extrabold tracking-tight">Trending Topics</h2>
        <span className="badge badge-pink">Live</span>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton h-36 rounded-2xl" />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-8">
          <p style={{ color: "var(--color-text-muted)" }}>Unable to load trends. Backend may be offline.</p>
        </div>
      ) : trends.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-3">📊</div>
          <p className="font-semibold mb-1">No Trends Yet</p>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            Trends appear after content is collected and analyzed. Run the ingestion worker to populate data.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {trends.map((trend, idx) => {
            const colors = [
              "var(--color-accent)",
              "var(--color-accent-2)",
              "var(--color-accent-3)",
              "var(--color-accent-4)",
              "var(--color-accent-5)",
            ];
            const accent = colors[idx % colors.length];

            return (
              <div
                key={trend.id}
                className="card group"
                style={{ borderTop: `2px solid ${accent}` }}
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-base font-bold capitalize" style={{ color: "var(--color-text)" }}>
                    {trend.name}
                  </h3>
                  <span
                    className="text-lg font-extrabold tabular-nums"
                    style={{ color: accent }}
                  >
                    {trend.trend_score}
                  </span>
                </div>

                {/* Mini bar chart visual */}
                <div className="flex items-end gap-1 h-8 mb-3">
                  {[trend.velocity, trend.engagement, trend.authority].map((v, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-t transition-all duration-500"
                      style={{
                        height: `${Math.max((v / 10) * 100, 10)}%`,
                        background: accent,
                        opacity: 0.3 + i * 0.25,
                      }}
                    />
                  ))}
                </div>

                <div className="flex items-center justify-between text-xs" style={{ color: "var(--color-text-muted)" }}>
                  <span>{trend.content_count} items</span>
                  <div className="flex gap-2">
                    <span title="Velocity">⚡ {trend.velocity}</span>
                    <span title="Engagement">💬 {trend.engagement}</span>
                    <span title="Authority">🏛️ {trend.authority}</span>
                  </div>
                </div>

                {/* Keywords */}
                {trend.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {trend.keywords.slice(0, 4).map((kw) => (
                      <span key={kw} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: "var(--color-surface-2)", color: "var(--color-text-muted)" }}>
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
