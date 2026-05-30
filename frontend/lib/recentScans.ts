import type { AnalyzeResponse } from "@/lib/api";

const RECENT_SCANS_KEY = "trustlens-recent-scans";
const RECENT_SCANS_LIMIT = 5;

export type RecentScanSource = "link" | "text";

export interface RecentScanItem {
  id: string;
  source: RecentScanSource;
  excerpt: string;
  trustScore: number;
  verdictEn: string;
  verdictBn: string;
  createdAt: string;
}

export function loadRecentScans(): RecentScanItem[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(RECENT_SCANS_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveRecentScan(content: string, result: Pick<AnalyzeResponse, "trust_score" | "verdict" | "verdict_bn">) {
  if (typeof window === "undefined") {
    return;
  }

  const item: RecentScanItem = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    source: isUrl(content) ? "link" : "text",
    excerpt: buildExcerpt(content),
    trustScore: Math.round(result.trust_score),
    verdictEn: result.verdict,
    verdictBn: result.verdict_bn,
    createdAt: new Date().toISOString(),
  };

  const existing = loadRecentScans();
  const next = [item, ...existing]
    .filter((entry, index, items) => items.findIndex((candidate) => candidate.excerpt === entry.excerpt && candidate.verdictEn === entry.verdictEn) === index)
    .slice(0, RECENT_SCANS_LIMIT);

  window.localStorage.setItem(RECENT_SCANS_KEY, JSON.stringify(next));
}

function isUrl(content: string) {
  return /https?:\/\/[^\s]+/i.test(content.trim());
}

function buildExcerpt(content: string) {
  const trimmed = content.trim().replace(/\s+/g, " ");

  if (isUrl(trimmed)) {
    try {
      const url = new URL(trimmed);
      return `${url.hostname}${url.pathname === "/" ? "" : url.pathname}`.slice(0, 72);
    } catch {
      return trimmed.slice(0, 72);
    }
  }

  return trimmed.slice(0, 72);
}