/**
 * API client for TrustLens backend.
 * Uses Next.js API routes as proxy to avoid CORS.
 */

export interface AnalyzeRequest {
  content: string;
  image_url?: string;
}

export interface PillarScore {
  name: string;
  name_bn: string;
  score: number;
  weight: number;
  explanation_en: string;
  explanation_bn: string;
  evidence: string[];
  model_used: string;
  active: boolean;
}

export interface AnalyzeResponse {
  trust_score: number;
  verdict: string;
  verdict_bn: string;
  pillars: PillarScore[];
  explanation_en: string;
  explanation_bn: string;
  confidence: number;
  cached: boolean;
  processing_time_ms: number;
  // Scrape-failure signaling (URL could not be retrieved)
  scrape_failed?: boolean;
  scrape_reason_en?: string;
  scrape_reason_bn?: string;
  needs_user_input?: boolean;
  original_url?: string;
}

export async function analyzeContent(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}
