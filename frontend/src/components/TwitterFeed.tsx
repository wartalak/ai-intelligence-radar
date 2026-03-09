"use client";

import { useContent } from "@/hooks/useApi";

export function TwitterFeed() {
  const { items, loading, error } = useContent("tweet", 12);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 rounded-full" style={{ background: "#1da1f2" }} />
        <h2 className="text-2xl font-extrabold tracking-tight">AI on 𝕏</h2>
        <span
          className="badge"
          style={{ background: "rgba(29,161,242,0.1)", color: "#1da1f2" }}
        >
          Corporate Accounts
        </span>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton h-40 rounded-2xl" />
          ))}
        </div>
      ) : error ? (
        <div className="card text-center py-8">
          <p style={{ color: "var(--color-text-muted)" }}>Unable to load tweets.</p>
        </div>
      ) : items.length === 0 ? (
        <div className="card text-center py-12">
          <div className="text-4xl mb-3">𝕏</div>
          <p className="font-semibold mb-1">No Tweets Yet</p>
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            Tweets from @AnthropicAI, @OpenAI, @GoogleDeepMind and other AI companies will appear here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((tweet) => {
            const handle = tweet.title || `@${tweet.author}`;
            const likes = tweet.engagement?.likes || 0;
            const retweets = tweet.engagement?.retweets || 0;
            const impressions = tweet.engagement?.impressions || 0;
            const company = (tweet.metadata as Record<string, unknown>)?.company as string || tweet.author;

            return (
              <a
                key={tweet.id}
                href={tweet.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="card group cursor-pointer transition-all duration-300 hover:scale-[1.02]"
                style={{ borderLeft: "3px solid #1da1f2" }}
              >
                {/* Header */}
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                    style={{ background: "linear-gradient(135deg, #1da1f2, #0d8ecf)" }}
                  >
                    {company.charAt(0)}
                  </div>
                  <div>
                    <p className="text-xs font-bold" style={{ color: "var(--color-text)" }}>
                      {company}
                    </p>
                    <p className="text-[10px]" style={{ color: "#1da1f2" }}>
                      {handle}
                    </p>
                  </div>
                  <span className="ml-auto text-[10px]" style={{ color: "var(--color-text-dim)" }}>
                    {tweet.published_at
                      ? new Date(tweet.published_at).toLocaleDateString("tr-TR", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : ""}
                  </span>
                </div>

                {/* Tweet body */}
                <p
                  className="text-sm leading-relaxed mb-3 line-clamp-4"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {tweet.body}
                </p>

                {/* Engagement */}
                <div className="flex items-center gap-3 text-[10px]" style={{ color: "var(--color-text-dim)" }}>
                  {likes > 0 && <span>♥ {likes.toLocaleString()}</span>}
                  {retweets > 0 && <span>🔄 {retweets.toLocaleString()}</span>}
                  {impressions > 0 && <span>👁 {impressions.toLocaleString()}</span>}
                </div>
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}
