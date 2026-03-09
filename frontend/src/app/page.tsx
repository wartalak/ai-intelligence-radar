"use client";

import { HeroReport } from "@/components/HeroReport";
import { SearchAnalysis } from "@/components/SearchAnalysis";
import { TrendingTopics } from "@/components/TrendingTopics";
import { ContentFeed } from "@/components/ContentFeed";
import { ResearchPapers } from "@/components/ResearchPapers";
import { TopVideos } from "@/components/TopVideos";
import { Navbar } from "@/components/Navbar";

export default function Home() {
  return (
    <main className="min-h-screen">
      <Navbar />

      {/* Hero: Today's Report */}
      <section id="today" className="pt-24 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <HeroReport />
      </section>

      {/* Search & Analysis */}
      <section id="search" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <SearchAnalysis />
      </section>

      {/* Trending Topics */}
      <section id="trends" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <TrendingTopics />
      </section>

      {/* Research Papers */}
      <section id="research" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <ResearchPapers />
      </section>

      {/* Top Videos */}
      <section id="videos" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <TopVideos />
      </section>

      {/* Latest Content Feed */}
      <section id="feed" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <ContentFeed />
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full" style={{ background: "var(--gradient-hero)" }} />
            <span className="text-sm font-semibold" style={{ color: "var(--color-text-muted)" }}>
              AI Intelligence Radar
            </span>
          </div>
          <p className="text-xs" style={{ color: "var(--color-text-dim)" }}>
            Powered by real-time data collection &amp; AI analysis. Data refreshes every 2 hours.
          </p>
        </div>
      </footer>
    </main>
  );
}
