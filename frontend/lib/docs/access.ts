import { DocsAccessState, DocsVisibilityConfig } from "@/lib/docs/types";

export function resolvePublishWindow(config: DocsVisibilityConfig): { start: Date; end: Date } {
  const start = new Date(config.startAtIso);

  if (config.mode === "duration") {
    const durationMs = Math.max(1, config.durationHours) * 60 * 60 * 1000;
    return { start, end: new Date(start.getTime() + durationMs) };
  }

  return { start, end: new Date(config.endAtIso) };
}

export function evaluateDocsAccess(config: DocsVisibilityConfig, nowDate = new Date()): DocsAccessState {
  const now = nowDate.getTime();
  const { start, end } = resolvePublishWindow(config);

  if (!config.enabled) {
    return {
      isPublic: false,
      reason: "disabled",
      nowIso: nowDate.toISOString(),
      startsInMs: start.getTime() - now,
      endsInMs: end.getTime() - now,
    };
  }

  if (now < start.getTime()) {
    return {
      isPublic: false,
      reason: "before_window",
      nowIso: nowDate.toISOString(),
      startsInMs: start.getTime() - now,
      endsInMs: end.getTime() - now,
    };
  }

  if (now > end.getTime()) {
    return {
      isPublic: false,
      reason: "after_window",
      nowIso: nowDate.toISOString(),
      startsInMs: start.getTime() - now,
      endsInMs: end.getTime() - now,
    };
  }

  return {
    isPublic: true,
    reason: "active",
    nowIso: nowDate.toISOString(),
    startsInMs: start.getTime() - now,
    endsInMs: end.getTime() - now,
  };
}

export function assertAdminToken(tokenHeader: string | null): boolean {
  const expected = process.env.DOCS_ADMIN_TOKEN || "trustlens-admin";
  return Boolean(tokenHeader && tokenHeader === expected);
}
