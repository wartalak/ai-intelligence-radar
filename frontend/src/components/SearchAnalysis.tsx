"use client";

import { useState } from "react";
import { useTopicAnalysis } from "@/hooks/useApi";

const SUGGESTIONS = [
  "AI agents",
  "open source LLMs",
  "OpenAI vs Anthropic competition",
  "AI startup funding",
  "latest research in transformers",
  "multimodal AI models",
  "AI regulation 2026",
  "RAG techniques",
];

export function SearchAnalysis() {
  const [query, setQuery] = useState("");
  const { analysis, loading, error, analyze } = useTopicAnalysis();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) analyze(query.trim());
  };

  const handleSuggestion = (s: string) => {
    setQuery(s);
    analyze(s);
  };

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-8 rounded-full" style={{ background: "var(--color-accent-2)" }} />
        <h2 className="text-2xl font-extrabold tracking-tight">Deep-Dive Analysis</h2>
      </div>

      {/* Search box */}
      <form onSubmit={handleSubmit} className="relative mb-4">
        <div className="glass rounded-2xl p-1 flex items-center gap-2 transition-all focus-within:border-[var(--color-accent)]" style={{ borderColor: "var(--color-border)" }}>
          <div className="pl-4">
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-text-muted)" }}>
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search any AI topic... e.g. &quot;AI agents&quot;, &quot;open source LLMs&quot;"
            className="flex-1 bg-transparent text-base py-3 px-2 outline-none placeholder:text-[var(--color-text-dim)]"
            style={{ color: "var(--color-text)" }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-2.5 rounded-xl text-sm font-bold text-white transition-all duration-200 disabled:opacity-40 hover:scale-105 active:scale-95 cursor-pointer"
            style={{
              background: loading ? "var(--color-surface-2)" : "var(--gradient-hero)",
            }}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
                Analyzing...
              </span>
            ) : (
              "Analyze"
            )}
          </button>
        </div>
      </form>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-2 mb-8">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSuggestion(s)}
            className="badge badge-purple transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="card mb-4" style={{ borderColor: "var(--color-danger)" }}>
          <p className="text-sm" style={{ color: "var(--color-danger)" }}>⚠️ {error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="card flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-4">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 rounded-full border-2 border-transparent animate-spin" style={{ borderTopColor: "var(--color-accent)", borderRightColor: "var(--color-accent-2)" }} />
              <div className="absolute inset-2 rounded-full border-2 border-transparent animate-spin" style={{ borderBottomColor: "var(--color-accent-3)", animationDirection: "reverse", animationDuration: "0.8s" }} />
              <div className="absolute inset-4 rounded-full" style={{ background: "var(--gradient-hero)", opacity: 0.3 }} />
            </div>
            <p className="text-sm font-medium" style={{ color: "var(--color-text-muted)" }}>
              Running deep analysis on &quot;{query}&quot;...
            </p>
          </div>
        </div>
      )}

      {/* Analysis result */}
      {analysis && !loading && (
        <div className="animate-fade-in space-y-4">
          <div className="card" style={{ borderTop: "2px solid var(--color-accent-2)" }}>
            <h3
              className="text-xl font-bold mb-3"
              style={{
                background: "linear-gradient(135deg, var(--color-accent-2), var(--color-accent-bright))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {analysis.title}
            </h3>
            <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-muted)" }}>
              {analysis.overview}
            </p>
          </div>

          {/* Analysis sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { key: "developments", label: "Key Developments", icon: "🚀", color: "var(--color-accent-bright)" },
              { key: "players", label: "Key Players", icon: "🏢", color: "var(--color-accent-2)" },
              { key: "technical", label: "Technical Details", icon: "⚙️", color: "var(--color-accent-3)" },
              { key: "impact", label: "Market Impact", icon: "📊", color: "var(--color-accent-4)" },
              { key: "outlook", label: "Outlook", icon: "🔮", color: "var(--color-accent-5)" },
            ].map(({ key, label, icon, color }) => {
              const items = (analysis as unknown as Record<string, unknown>)[key] as Array<{ point: string; detail: string }> | undefined;
              if (!items || items.length === 0) return null;
              return (
                <div key={key} className="card" style={{ borderTop: `2px solid ${color}` }}>
                  <h4 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider mb-3" style={{ color }}>
                    <span>{icon}</span> {label}
                  </h4>
                  <ul className="space-y-2">
                    {items.map((item, i) => (
                      <li key={i}>
                        <p className="text-sm font-semibold" style={{ color: "var(--color-text)" }}>{item.point}</p>
                        <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>{item.detail}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>

          {/* Sources */}
          {analysis.sources && analysis.sources.length > 0 && (
            <div className="card">
              <h4 className="text-sm font-bold uppercase tracking-wider mb-3" style={{ color: "var(--color-text-muted)" }}>
                📎 Sources
              </h4>
              <div className="flex flex-wrap gap-2">
                {analysis.sources.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="badge badge-teal hover:scale-105 transition-transform cursor-pointer"
                  >
                    {src.title?.slice(0, 40) || src.type}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
