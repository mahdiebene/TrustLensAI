import { NextRequest, NextResponse } from "next/server";
import { assertAdminToken, evaluateDocsAccess, resolvePublishWindow } from "@/lib/docs/access";
import { readDocsConfig, writeDocsConfig } from "@/lib/docs/storage";
import { DocsVisibilityConfig } from "@/lib/docs/types";

export async function GET() {
  const config = await readDocsConfig();
  const access = evaluateDocsAccess(config);
  const window = resolvePublishWindow(config);

  return NextResponse.json({ config, access, window });
}

export async function PUT(request: NextRequest) {
  const token = request.headers.get("x-docs-admin-token");
  if (!assertAdminToken(token)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = (await request.json()) as Partial<DocsVisibilityConfig>;
  const current = await readDocsConfig();

  const next: DocsVisibilityConfig = {
    ...current,
    ...payload,
    updatedAtIso: new Date().toISOString(),
    updatedBy: "admin",
  };

  await writeDocsConfig(next);
  return NextResponse.json({ ok: true, config: next });
}
