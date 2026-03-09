/**
 * React hooks for API data fetching.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  fetchTodayReport,
  fetchTrends,
  fetchLatestContent,
  analyzeQuery,
  Report,
  TrendsResponse,
  ContentResponse,
  TopicAnalysis,
} from "@/lib/api";

// ── useTodayReport ──
export function useTodayReport() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTodayReport()
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { report, loading, error };
}

// ── useTrends ──
export function useTrends() {
  const [data, setData] = useState<TrendsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrends()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { trends: data?.trends ?? [], loading, error };
}

// ── useContent ──
export function useContent(type?: string, limit = 50) {
  const [data, setData] = useState<ContentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchLatestContent(type, limit)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [type, limit]);

  return { items: data?.items ?? [], count: data?.count ?? 0, loading, error };
}

// ── useTopicAnalysis ──
export function useTopicAnalysis() {
  const [analysis, setAnalysis] = useState<TopicAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const result = await analyzeQuery(query);
      setAnalysis(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }, []);

  return { analysis, loading, error, analyze };
}
