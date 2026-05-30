"use client";

import { useEffect, useMemo, useState } from "react";
import { DocsContent, DocsVisibilityConfig } from "@/lib/docs/types";

type LoadState = "auth" | "loading" | "ready" | "error";

const emptyContent: DocsContent = {
  updatedAtIso: "",
  version: "",
  teamName: "",
  deck: [],
  productOverview: "",
  architectureMermaid: "",
  dataFlowMermaid: "",
  technologyStack: {},
  apiDocumentation: "",
  dataLayer: "",
  aiLayer: "",
  roadmap: { short_term: [], mid_term: [], long_term: [] },
  performance: "",
  security: "",
  analytics: "",
  changelog: [],
  teamMembers: [],
  features: [],
};

const emptyConfig: DocsVisibilityConfig = {
  enabled: false,
  mode: "window",
  startAtIso: "",
  endAtIso: "",
  durationHours: 24,
  updatedAtIso: "",
  updatedBy: "",
};

export default function DocsAdminPage() {
  const [state, setState] = useState<LoadState>("auth");
  const [token, setToken] = useState("");
  const [content, setContent] = useState<DocsContent>(emptyContent);
  const [config, setConfig] = useState<DocsVisibilityConfig>(emptyConfig);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const saved = sessionStorage.getItem("docs-admin-token");
    if (saved) {
      setToken(saved);
      void authenticate(saved);
    }
  }, []);

  const canSave = useMemo(() => state === "ready" && token.length > 0, [state, token]);

  async function authenticate(currentToken: string) {
    setState("loading");
    setMessage("");

    const verify = await fetch("/api/docs/admin/verify", {
      method: "POST",
      headers: { "x-docs-admin-token": currentToken },
    });

    if (!verify.ok) {
      setState("auth");
      setMessage("Invalid admin token");
      return;
    }

    sessionStorage.setItem("docs-admin-token", currentToken);

    const [contentRes, configRes] = await Promise.all([
      fetch("/api/docs/content"),
      fetch("/api/docs/config"),
    ]);

    if (!contentRes.ok || !configRes.ok) {
      setState("error");
      setMessage("Failed to load docs data");
      return;
    }

    const contentPayload = await contentRes.json();
    const configPayload = await configRes.json();

    setContent(contentPayload.content as DocsContent);
    setConfig(configPayload.config as DocsVisibilityConfig);
    setState("ready");
  }

  async function saveDraft() {
    setMessage("Saving draft...");

    const [contentRes, configRes] = await Promise.all([
      fetch("/api/docs/content", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "x-docs-admin-token": token,
        },
        body: JSON.stringify(content),
      }),
      fetch("/api/docs/config", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "x-docs-admin-token": token,
        },
        body: JSON.stringify(config),
      }),
    ]);

    if (!contentRes.ok || !configRes.ok) {
      setMessage("Failed to save draft");
      return;
    }

    setMessage("Draft saved");
  }

  async function publishNow() {
    setMessage("Publishing...");

    const response = await fetch("/api/docs/publish", {
      method: "POST",
      headers: { "x-docs-admin-token": token },
    });

    if (!response.ok) {
      setMessage("Failed to publish");
      return;
    }

    setMessage("Published snapshot created");
  }

  function updateDeck(index: number, key: "title" | "summary" | "details", value: string) {
    setContent((prev) => ({
      ...prev,
      deck: prev.deck.map((item, current) => (current === index ? { ...item, [key]: value } : item)),
    }));
  }

  function moveDeck(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= content.deck.length) {
      return;
    }

    setContent((prev) => {
      const next = [...prev.deck];
      const temp = next[index];
      next[index] = next[target];
      next[target] = temp;
      return { ...prev, deck: next };
    });
  }

  if (state === "auth") {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="section-surface p-8 w-full max-w-lg">
          <h1 className="text-page-section font-semibold heading-tight text-text-primary">Docs Admin</h1>
          <p className="text-body text-text-secondary mt-2">Enter admin token to manage /docs publishing and content.</p>
          <input
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            className="w-full mt-4 rounded-xl border border-surface-3/60 bg-surface-1 px-4 py-3"
            placeholder="Admin token"
          />
          <button
            onClick={() => void authenticate(token)}
            className="mt-4 px-4 py-2 rounded-xl bg-accent-blue text-white"
          >
            Authenticate
          </button>
          {message ? <p className="text-caption text-trust-low mt-2">{message}</p> : null}
        </div>
      </div>
    );
  }

  if (state === "loading") {
    return <div className="py-20 text-center text-text-secondary">Loading docs admin...</div>;
  }

  if (state === "error") {
    return <div className="py-20 text-center text-trust-low">{message || "Admin load error"}</div>;
  }

  return (
    <div className="flex flex-col gap-6 md:gap-8">
      <header className="section-surface p-6">
        <h1 className="text-page-section font-semibold heading-tight text-text-primary">Docs Admin Controls</h1>
        <p className="text-body text-text-secondary mt-2">Visibility scheduling, pitch deck editing, team showcase, and publishing controls.</p>
        <div className="flex flex-wrap gap-2 mt-4">
          <button onClick={saveDraft} disabled={!canSave} className="px-4 py-2 rounded-xl bg-surface-1 border border-surface-3/60 text-text-primary">Save Draft</button>
          <button onClick={publishNow} disabled={!canSave} className="px-4 py-2 rounded-xl bg-accent-blue text-white">Publish Snapshot</button>
          <a href="/docs" target="_blank" rel="noreferrer" className="px-4 py-2 rounded-xl bg-surface-1 border border-surface-3/60 text-text-primary">Open Public Docs</a>
        </div>
        {message ? <p className="text-caption text-text-tertiary mt-3">{message}</p> : null}
      </header>

      <section className="section-surface p-6">
        <h2 className="text-section-header font-semibold text-text-primary">Access Control and Scheduling</h2>
        <div className="grid gap-3 md:grid-cols-2 mt-4">
          <label className="flex items-center gap-2 text-body text-text-primary">
            <input type="checkbox" checked={config.enabled} onChange={(event) => setConfig((prev) => ({ ...prev, enabled: event.target.checked }))} />
            Docs visibility enabled
          </label>
          <label className="text-body text-text-primary">
            Mode
            <select
              value={config.mode}
              onChange={(event) => setConfig((prev) => ({ ...prev, mode: event.target.value as "window" | "duration" }))}
              className="w-full mt-1 rounded-xl border border-surface-3/60 bg-surface-1 px-3 py-2"
            >
              <option value="window">Start + End window</option>
              <option value="duration">Start + Duration</option>
            </select>
          </label>
          <label className="text-body text-text-primary">
            Start date/time
            <input
              type="datetime-local"
              value={toInputDate(config.startAtIso)}
              onChange={(event) => setConfig((prev) => ({ ...prev, startAtIso: new Date(event.target.value).toISOString() }))}
              className="w-full mt-1 rounded-xl border border-surface-3/60 bg-surface-1 px-3 py-2"
            />
          </label>
          {config.mode === "window" ? (
            <label className="text-body text-text-primary">
              End date/time
              <input
                type="datetime-local"
                value={toInputDate(config.endAtIso)}
                onChange={(event) => setConfig((prev) => ({ ...prev, endAtIso: new Date(event.target.value).toISOString() }))}
                className="w-full mt-1 rounded-xl border border-surface-3/60 bg-surface-1 px-3 py-2"
              />
            </label>
          ) : (
            <label className="text-body text-text-primary">
              Duration hours
              <input
                type="number"
                min={1}
                value={config.durationHours}
                onChange={(event) => setConfig((prev) => ({ ...prev, durationHours: Number(event.target.value) || 1 }))}
                className="w-full mt-1 rounded-xl border border-surface-3/60 bg-surface-1 px-3 py-2"
              />
            </label>
          )}
        </div>
      </section>

      <section className="section-surface p-6">
        <h2 className="text-section-header font-semibold text-text-primary">Deck Sections</h2>
        <div className="grid gap-4 mt-4">
          {content.deck.map((item, index) => (
            <article key={item.id} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
              <div className="flex justify-between items-center mb-2">
                <p className="text-body font-medium text-text-primary">{item.id}</p>
                <div className="flex gap-2">
                  <button onClick={() => moveDeck(index, -1)} className="px-3 py-1 rounded-lg border border-surface-3/60">Up</button>
                  <button onClick={() => moveDeck(index, 1)} className="px-3 py-1 rounded-lg border border-surface-3/60">Down</button>
                </div>
              </div>
              <input value={item.title} onChange={(event) => updateDeck(index, "title", event.target.value)} className="w-full rounded-lg border border-surface-3/60 bg-surface-2 px-3 py-2" />
              <textarea value={item.summary} onChange={(event) => updateDeck(index, "summary", event.target.value)} rows={2} className="w-full mt-2 rounded-lg border border-surface-3/60 bg-surface-2 px-3 py-2" />
              <textarea value={item.details} onChange={(event) => updateDeck(index, "details", event.target.value)} rows={3} className="w-full mt-2 rounded-lg border border-surface-3/60 bg-surface-2 px-3 py-2" />
            </article>
          ))}
        </div>
      </section>

      <section className="section-surface p-6">
        <h2 className="text-section-header font-semibold text-text-primary">Core Technical Sections</h2>
        <EditorField label="Version" value={content.version} onChange={(value) => setContent((prev) => ({ ...prev, version: value }))} />
        <EditorField label="Product Overview" multiline value={content.productOverview} onChange={(value) => setContent((prev) => ({ ...prev, productOverview: value }))} />
        <EditorField label="Architecture Mermaid" multiline value={content.architectureMermaid} onChange={(value) => setContent((prev) => ({ ...prev, architectureMermaid: value }))} />
        <EditorField label="Data Flow Mermaid" multiline value={content.dataFlowMermaid} onChange={(value) => setContent((prev) => ({ ...prev, dataFlowMermaid: value }))} />
        <EditorField label="API Documentation" multiline value={content.apiDocumentation} onChange={(value) => setContent((prev) => ({ ...prev, apiDocumentation: value }))} />
        <EditorField label="Data Layer" multiline value={content.dataLayer} onChange={(value) => setContent((prev) => ({ ...prev, dataLayer: value }))} />
        <EditorField label="AI Layer" multiline value={content.aiLayer} onChange={(value) => setContent((prev) => ({ ...prev, aiLayer: value }))} />
        <EditorField label="Performance" multiline value={content.performance} onChange={(value) => setContent((prev) => ({ ...prev, performance: value }))} />
        <EditorField label="Security" multiline value={content.security} onChange={(value) => setContent((prev) => ({ ...prev, security: value }))} />
        <EditorField label="Analytics" multiline value={content.analytics} onChange={(value) => setContent((prev) => ({ ...prev, analytics: value }))} />
      </section>

      <section className="section-surface p-6">
        <h2 className="text-section-header font-semibold text-text-primary">Team Showcase</h2>
        <EditorField label="Team Name" value={content.teamName} onChange={(value) => setContent((prev) => ({ ...prev, teamName: value }))} />
        <div className="grid gap-4 mt-4 md:grid-cols-2">
          {content.teamMembers.map((member, index) => (
            <article key={member.id} className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
              <EditorField label="Full Name" value={member.name} onChange={(value) => updateTeam(index, "name", value)} compact />
              <EditorField label="Role" value={member.role} onChange={(value) => updateTeam(index, "role", value)} compact />
              <EditorField label="Email" value={member.email} onChange={(value) => updateTeam(index, "email", value)} compact />
              <EditorField label="Photo URL" value={member.photoUrl} onChange={(value) => updateTeam(index, "photoUrl", value)} compact />
            </article>
          ))}
        </div>
      </section>
    </div>
  );

  function updateTeam(index: number, key: "name" | "role" | "email" | "photoUrl", value: string) {
    setContent((prev) => ({
      ...prev,
      teamMembers: prev.teamMembers.map((item, current) => (current === index ? { ...item, [key]: value } : item)),
    }));
  }
}

function toInputDate(value: string) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  const pad = (num: number) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function EditorField({
  label,
  value,
  onChange,
  multiline = false,
  compact = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
  compact?: boolean;
}) {
  return (
    <label className={`block ${compact ? "mt-2" : "mt-4"}`}>
      <span className="text-body text-text-primary">{label}</span>
      {multiline ? (
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          rows={4}
          className="w-full mt-1 rounded-xl border border-surface-3/60 bg-surface-1 px-3 py-2"
        />
      ) : (
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full mt-1 rounded-xl border border-surface-3/60 bg-surface-1 px-3 py-2"
        />
      )}
    </label>
  );
}
