import { readFile } from "fs/promises";
import path from "path";
import { DocsContent, DocsLiveState, DocsVersionSnapshot } from "@/lib/docs/types";

export async function getDocsLiveState(content: DocsContent, versions: DocsVersionSnapshot[]): Promise<DocsLiveState> {
  const pkgPath = path.join(process.cwd(), "package.json");
  let appVersion = "0.0.0";

  try {
    const pkgRaw = await readFile(pkgPath, "utf8");
    const pkg = JSON.parse(pkgRaw) as { version?: string };
    appVersion = pkg.version || appVersion;
  } catch {
    appVersion = "0.0.0";
  }

  let backendHealth: "ok" | "degraded" = "degraded";
  let backendDetails: Record<string, string> = { status: "unreachable" };

  try {
    const backendUrl = process.env.API_URL || "http://localhost:8000";
    const response = await fetch(`${backendUrl}/api/health`, {
      method: "GET",
      cache: "no-store",
    });

    if (response.ok) {
      const data = (await response.json()) as { status?: string; services?: Record<string, string> };
      backendHealth = data.status === "ok" ? "ok" : "degraded";
      backendDetails = data.services || { status: data.status || "ok" };
    }
  } catch {
    backendHealth = "degraded";
    backendDetails = { status: "unreachable" };
  }

  const liveFeatureCount = content.features.filter((item) => item.status === "live").length;
  const upcomingFeatureCount = content.features.filter((item) => item.status === "upcoming").length;
  const plannedFeatureCount = content.features.filter((item) => item.status === "planned").length;

  return {
    serverTimeIso: new Date().toISOString(),
    appVersion,
    backendHealth,
    backendDetails,
    lastPublishIso: versions[0]?.createdAtIso || "",
    totalVersions: versions.length,
    liveFeatureCount,
    upcomingFeatureCount,
    plannedFeatureCount,
  };
}
