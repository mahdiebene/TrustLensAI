import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://localhost:8000";

// Allow up to 90s for the backend (perplexity-reasoning can take 30-60s)
export const maxDuration = 90;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // 85s client-side abort, leaves ~5s headroom under maxDuration
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 85_000);

    let response: Response;
    try {
      response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeout);
    }

    if (!response.ok) {
      // Try to forward the backend's error body if it's JSON
      let errBody: any = { error: "Analysis failed" };
      try {
        errBody = await response.json();
      } catch {
        // ignore
      }
      return NextResponse.json(errBody, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    const isAbort = error?.name === "AbortError";
    return NextResponse.json(
      {
        error: isAbort
          ? "Analysis took too long — please try again."
          : "Failed to connect to analysis service",
      },
      { status: isAbort ? 504 : 503 }
    );
  }
}
