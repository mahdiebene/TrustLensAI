"use client";

import { useEffect, useRef, useState } from "react";

interface MermaidDiagramProps {
  chart: string;
}

export function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function render() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({ startOnLoad: false, securityLevel: "loose", theme: "base" });
        const id = `diagram-${Math.random().toString(36).slice(2)}`;
        const rendered = await mermaid.render(id, chart);
        if (active && ref.current) {
          ref.current.innerHTML = rendered.svg;
          setError("");
        }
      } catch {
        if (active) {
          setError("Unable to render diagram");
        }
      }
    }

    render();

    return () => {
      active = false;
    };
  }, [chart]);

  if (error) {
    return (
      <div className="rounded-2xl border border-trust-low/30 bg-trust-low/10 p-4 text-caption text-trust-low">
        {error}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4 overflow-x-auto">
      <div ref={ref} />
    </div>
  );
}
