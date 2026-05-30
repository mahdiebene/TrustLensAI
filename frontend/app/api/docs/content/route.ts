import { NextRequest, NextResponse } from "next/server";
import { assertAdminToken } from "@/lib/docs/access";
import { readDocsContent, writeDocsContent } from "@/lib/docs/storage";
import { DocsContent } from "@/lib/docs/types";

export async function GET() {
  const content = await readDocsContent();
  return NextResponse.json({ content });
}

export async function PUT(request: NextRequest) {
  const token = request.headers.get("x-docs-admin-token");
  if (!assertAdminToken(token)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const payload = (await request.json()) as DocsContent;
  const next: DocsContent = {
    ...payload,
    updatedAtIso: new Date().toISOString(),
  };

  await writeDocsContent(next);
  return NextResponse.json({ ok: true, content: next });
}
