"use client";

import { useMemo, useState } from "react";
import { MermaidDiagram } from "@/components/MermaidDiagram";
import { DocsAccessState, DocsContent, DocsLiveState, DocsVisibilityConfig, DocsVersionSnapshot } from "@/lib/docs/types";

interface DocsClientProps {
  content: DocsContent;
  visibility: DocsVisibilityConfig;
  access: DocsAccessState;
  live: DocsLiveState;
  versions: DocsVersionSnapshot[];
}

const sectionOrder = [
  { id: "pitch", label: "Pitch Deck" },
  { id: "overview", label: "Product Overview" },
  { id: "features", label: "Feature Matrix" },
  { id: "architecture", label: "Architecture" },
  { id: "dataflow", label: "Data Flow" },
  { id: "stack", label: "Tech Stack" },
  { id: "api", label: "API" },
  { id: "data-layer", label: "Data Layer" },
  { id: "ai", label: "AI Layer" },
  { id: "roadmap", label: "Roadmap" },
  { id: "performance", label: "Performance" },
  { id: "security", label: "Security" },
  { id: "analytics", label: "Analytics" },
  { id: "team", label: "Team" },
  { id: "changelog", label: "Changelog" },
];

export function DocsClient({ content, visibility, access, live, versions }: DocsClientProps) {
  const [query, setQuery] = useState("");

  const queryMatches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return sectionOrder;
    }

    return sectionOrder.filter((section) => {
      const text = [
        section.label,
        content.productOverview,
        content.apiDocumentation,
        content.dataLayer,
        content.aiLayer,
        content.performance,
        content.security,
        content.analytics,
        ...content.deck.map((item) => `${item.title} ${item.summary} ${item.details}`),
      ].join(" ").toLowerCase();

      return text.includes(normalized);
    });
  }, [content, query]);

  return (
    <div className="flex flex-col gap-8 md:gap-10">
      <header className="section-surface p-6 md:p-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <p className="text-caption text-text-tertiary uppercase caps-wide">Live Documentation</p>
            <h1 className="text-page-title font-semibold heading-tight text-text-primary mt-2">TrustLens Documentation and Pitch Deck</h1>
            <p className="text-body text-text-secondary mt-2 max-w-3xl">Understand the product in 2 minutes, evaluate architecture in 10 minutes, and verify live status in real time.</p>
          </div>
          <div className="flex items-center gap-2">
            <a href="/api/docs/export/markdown" className="px-4 py-2 rounded-xl border border-surface-3/60 bg-surface-1 text-body text-text-primary">Export Markdown</a>
            <button onClick={() => window.print()} className="px-4 py-2 rounded-xl bg-accent-blue text-white text-body">Export PDF</button>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mt-6">
          <Metric label="Public Access" value={access.isPublic ? "ON" : "OFF"} />
          <Metric label="Window Start" value={new Date(visibility.startAtIso).toLocaleString()} />
          <Metric label="Window End" value={new Date(visibility.mode === "duration" ? new Date(visibility.startAtIso).getTime() + visibility.durationHours * 3600000 : new Date(visibility.endAtIso)).toLocaleString()} />
          <Metric label="Backend Health" value={live.backendHealth.toUpperCase()} />
        </div>

        <div className="mt-6">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search docs sections"
            className="w-full rounded-xl border border-surface-3/60 bg-surface-1 px-4 py-3 text-body text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue/20"
          />
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[250px_1fr] items-start">
        <aside className="section-surface p-4 sticky top-24">
          <p className="text-caption uppercase caps-wide text-text-tertiary mb-3">Section Navigation</p>
          <nav className="flex flex-col gap-2">
            {queryMatches.map((item) => (
              <a key={item.id} href={`#${item.id}`} className="text-body text-text-secondary hover:text-text-primary">
                {item.label}
              </a>
            ))}
          </nav>
          <a href="/docs/admin" className="inline-block mt-6 text-caption text-accent-blue hover:underline">Open Admin Panel</a>
        </aside>

        <main className="flex flex-col gap-8">
          <section id="pitch" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">YC-Style Pitch Deck</h2>
            <div className="grid gap-3 mt-4 md:grid-cols-2">
              {content.deck.map((section) => (
                <article key={section.id} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
                  <h3 className="text-section-header font-semibold text-text-primary">{section.title}</h3>
                  <p className="text-body text-text-secondary mt-2">{section.summary}</p>
                  <p className="text-caption text-text-tertiary mt-2">{section.details}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="overview" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Product Overview</h2>
            <p className="text-body text-text-secondary mt-3">{content.productOverview}</p>
          </section>

          <section id="features" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Feature Matrix (Live Synced)</h2>
            <div className="grid gap-3 mt-4">
              {content.features.map((feature) => (
                <div key={feature.id} className="rounded-2xl border border-surface-3/60 bg-surface-1 px-4 py-3 flex items-center justify-between gap-4">
                  <div>
                    <p className="text-body text-text-primary">{feature.name}</p>
                    <p className="text-caption text-text-tertiary">{feature.note}</p>
                  </div>
                  <StatusBadge status={feature.status} />
                </div>
              ))}
            </div>
          </section>

          <section id="architecture" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Architecture Diagram</h2>
            <MermaidDiagram chart={content.architectureMermaid} />
          </section>

          <section id="dataflow" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Data Flow Diagram</h2>
            <MermaidDiagram chart={content.dataFlowMermaid} />
          </section>

          <section id="stack" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Technology Stack</h2>
            <div className="grid gap-3 md:grid-cols-2 mt-4">
              {Object.entries(content.technologyStack).map(([key, values]) => (
                <div key={key} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
                  <p className="text-section-header font-semibold text-text-primary capitalize">{key}</p>
                  <ul className="mt-2 space-y-1">
                    {values.map((value) => (
                      <li key={value} className="text-caption text-text-secondary">- {value}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <section id="api" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">API Documentation</h2>
            <p className="text-body text-text-secondary mt-3">{content.apiDocumentation}</p>
          </section>

          <section id="data-layer" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Data Layer</h2>
            <p className="text-body text-text-secondary mt-3">{content.dataLayer}</p>
          </section>

          <section id="ai" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">AI Layer</h2>
            <p className="text-body text-text-secondary mt-3">{content.aiLayer}</p>
          </section>

          <section id="roadmap" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Product Roadmap</h2>
            <div className="grid gap-3 md:grid-cols-3 mt-4">
              {Object.entries(content.roadmap).map(([phase, items]) => (
                <div key={phase} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
                  <p className="text-section-header font-semibold text-text-primary capitalize">{phase.replace("_", " ")}</p>
                  <ul className="mt-2 space-y-1">
                    {items.map((item) => (
                      <li key={item} className="text-caption text-text-secondary">- {item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <section id="performance" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Performance and Scalability</h2>
            <p className="text-body text-text-secondary mt-3">{content.performance}</p>
          </section>

          <section id="security" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Security</h2>
            <p className="text-body text-text-secondary mt-3">{content.security}</p>
          </section>

          <section id="analytics" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Analytics</h2>
            <p className="text-body text-text-secondary mt-3">{content.analytics}</p>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mt-4">
              <Metric label="Versions" value={String(live.totalVersions)} />
              <Metric label="Live Features" value={String(live.liveFeatureCount)} />
              <Metric label="Upcoming" value={String(live.upcomingFeatureCount)} />
              <Metric label="Planned" value={String(live.plannedFeatureCount)} />
            </div>
          </section>

          <section id="team" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Team and Contributors</h2>
            <p className="text-body text-text-secondary mt-2">{content.teamName}</p>
            <div className="grid gap-4 mt-4 sm:grid-cols-2 lg:grid-cols-3">
              {content.teamMembers.map((member) => (
                <article key={member.id} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
                  <div className="h-28 w-28 rounded-2xl bg-surface-2 border border-surface-3/70 overflow-hidden mx-auto">
                    {member.photoUrl ? (
                      <img src={member.photoUrl} alt={member.name} className="h-full w-full object-cover" />
                    ) : (
                      <div className="h-full w-full flex items-center justify-center text-page-section text-text-tertiary font-semibold">
                        {initials(member.name)}
                      </div>
                    )}
                  </div>
                  <p className="text-section-header font-semibold text-text-primary mt-3 text-center">{member.name}</p>
                  <p className="text-body text-text-secondary text-center">{member.role}</p>
                  <p className="text-caption text-text-tertiary text-center mt-1">{member.email}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="changelog" className="section-surface p-5 md:p-7">
            <h2 className="text-page-section font-semibold heading-tight text-text-primary">Changelog</h2>
            <div className="grid gap-3 mt-4">
              {content.changelog.map((item) => (
                <article key={`${item.version}-${item.dateIso}`} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
                  <p className="text-body font-medium text-text-primary">{item.version}</p>
                  <p className="text-caption text-text-tertiary mt-1">{new Date(item.dateIso).toLocaleString()}</p>
                  <p className="text-body text-text-secondary mt-2">{item.notes}</p>
                </article>
              ))}
              {versions.slice(0, 5).map((version) => (
                <article key={version.id} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
                  <p className="text-body font-medium text-text-primary">Published Snapshot</p>
                  <p className="text-caption text-text-tertiary mt-1">{new Date(version.createdAtIso).toLocaleString()} by {version.createdBy}</p>
                  <p className="text-caption text-text-secondary mt-2">Version {version.content.version}</p>
                </article>
              ))}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function initials(value: string) {
  return value
    .split(" ")
    .map((item) => item[0] || "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-surface-3/60 bg-surface-1 px-4 py-3">
      <p className="text-caption text-text-tertiary">{label}</p>
      <p className="text-body font-medium text-text-primary mt-1">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: "live" | "upcoming" | "planned" }) {
  const style = status === "live"
    ? "bg-trust-high/10 text-trust-high"
    : status === "upcoming"
      ? "bg-trust-medium/10 text-trust-medium"
      : "bg-accent-blue/10 text-accent-blue";

  return <span className={`px-3 py-1 rounded-full text-caption font-medium ${style}`}>{status}</span>;
}
