import { NextResponse } from "next/server";
import { getDocsLiveState } from "@/lib/docs/live";
import { readDocsContent, readDocsVersions } from "@/lib/docs/storage";

export async function GET() {
  const [content, versions] = await Promise.all([readDocsContent(), readDocsVersions()]);
  const live = await getDocsLiveState(content, versions);

  return NextResponse.json({ live });
}
