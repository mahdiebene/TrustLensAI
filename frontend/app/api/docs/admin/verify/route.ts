import { NextRequest, NextResponse } from "next/server";
import { assertAdminToken } from "@/lib/docs/access";

export async function POST(request: NextRequest) {
  const token = request.headers.get("x-docs-admin-token");
  if (!assertAdminToken(token)) {
    return NextResponse.json({ ok: false }, { status: 401 });
  }

  return NextResponse.json({ ok: true });
}
