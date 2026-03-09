/**
 * API client configuration for the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ── Report ──
export interface ReportSection {
  headline: string;
  detail: string;
  sources?: string[];
}

export interface Report {
  id?: number;
  date: string;
  title: string;
  summary: string;
  sections: {
    announcements?: ReportSection[];
    breakthroughs?: ReportSection[];
    tools?: ReportSection[];
    discussions?: ReportSection[];
    insights?: ReportSection[];
  };
  source_refs?: Array<{ title: string; url: string }>;
}

export async function fetchTodayReport(): Promise<Report> {
  return fetchApi<Report>("/report/today");
}

// ── Trends ──
export interface TrendItem {
  id: number;
  name: string;
  description?: string;
  keywords: string[];
  content_count: number;
  trend_score: number;
  velocity: number;
  engagement: number;
  authority: number;
}

export interface TrendsResponse {
  trends: TrendItem[];
}

export async function fetchTrends(): Promise<TrendsResponse> {
  return fetchApi<TrendsResponse>("/trends");
}

// ── Content ──
export interface ContentItem {
  id: number;
  title: string;
  body: string;
  url: string;
  author: string;
  published_at?: string;
  content_type: string;
  engagement: Record<string, number>;
  metadata: Record<string, unknown>;
  source: string;
}

export interface ContentResponse {
  items: ContentItem[];
  count: number;
}

export async function fetchLatestContent(
  type?: string,
  limit = 50
): Promise<ContentResponse> {
  const params = new URLSearchParams();
  if (type) params.set("content_type", type);
  params.set("limit", String(limit));
  return fetchApi<ContentResponse>(`/content/latest?${params}`);
}

// ── Topic Analysis ──
export interface AnalysisPoint {
  point: string;
  detail: string;
  source?: string;
}

export interface TopicAnalysis {
  query: string;
  title: string;
  overview: string;
  developments?: AnalysisPoint[];
  players?: AnalysisPoint[];
  technical?: AnalysisPoint[];
  impact?: AnalysisPoint[];
  outlook?: AnalysisPoint[];
  sources?: Array<{ title: string; url: string; type: string }>;
}

export async function analyzeQuery(query: string): Promise<TopicAnalysis> {
  return fetchApi<TopicAnalysis>("/analysis/topic", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}
