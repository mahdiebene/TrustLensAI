import { NextResponse } from "next/server";
import { readDocsContent } from "@/lib/docs/storage";

export async function GET() {
  const content = await readDocsContent();

  const markdown = [
    `# TrustLens Docs (${content.version})`,
    ``,
    `Updated: ${content.updatedAtIso}`,
    ``,
    `## Pitch Deck`,
    ...content.deck.flatMap((section) => [
      `### ${section.title}`,
      `${section.summary}`,
      ``,
      `${section.details}`,
      ``,
    ]),
    `## Product Overview`,
    content.productOverview,
    ``,
    `## API`,
    content.apiDocumentation,
    ``,
    `## Data Layer`,
    content.dataLayer,
    ``,
    `## AI Layer`,
    content.aiLayer,
    ``,
    `## Security`,
    content.security,
    ``,
    `## Team`,
    ...content.teamMembers.map((member) => `- ${member.name} | ${member.role} | ${member.email}`),
    ``,
    `## Changelog`,
    ...content.changelog.map((item) => `- ${item.version} (${item.dateIso}): ${item.notes}`),
  ].join("\n");

  return new NextResponse(markdown, {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": "attachment; filename=trustlens-docs.md",
    },
  });
}
