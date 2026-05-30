import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { assertAdminToken } from "@/lib/docs/access";
import { appendDocsVersion, readDocsContent } from "@/lib/docs/storage";

export async function POST(request: NextRequest) {
  const token = request.headers.get("x-docs-admin-token");
  if (!assertAdminToken(token)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const content = await readDocsContent();
  await appendDocsVersion({
    id: randomUUID(),
    createdAtIso: new Date().toISOString(),
    createdBy: "admin",
    content,
  });

  return NextResponse.json({ ok: true });
}
