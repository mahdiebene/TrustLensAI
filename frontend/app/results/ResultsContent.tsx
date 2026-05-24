"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useSearchParams } from "next/navigation";
import { TrustGauge } from "@/components/TrustGauge";
import { PillarCard } from "@/components/PillarCard";
import { RadarChart } from "@/components/RadarChart";
import { ScanAnimation } from "@/components/ScanAnimation";
import { useStore } from "@/lib/store";
import { analyzeContent } from "@/lib/api";

export function ResultsContent() {
  const { result, setResult, isAnalyzing, setIsAnalyzing, analysisStatus, setAnalysisStatus } = useStore();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const content = searchParams.get("content");
    if (content && !result && !isAnalyzing) {
      runAnalysis(content);
    }
  }, [searchParams]);

  async function runAnalysis(content: string) {
    setIsAnalyzing(true);
    setError(null);

    const statuses = [
      "Checking sources...",
      "Analyzing language patterns...",
      "Cross-referencing claims...",
      "Generating trust score...",
    ];

    let statusIndex = 0;
    const statusInterval = setInterval(() => {
      statusIndex = (statusIndex + 1) % statuses.length;
      setAnalysisStatus(statuses[statusIndex]);
    }, 2000);

    setAnalysisStatus(statuses[0]);

    try {
      const data = await analyzeContent({ content });
      setResult(data);
    } catch (e: any) {
      setError(e.message || "Analysis failed");
    } finally {
      clearInterval(statusInterval);
      setIsAnalyzing(false);
      setAnalysisStatus("");
    }
  }

  return (
    <div className="flex flex-col gap-12">
      {/* Header */}
      <header className="flex items-center justify-between pt-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-md bg-accent-blue flex items-center justify-center">
            <span className="text-white text-body font-semibold">T</span>
          </div>
          <h1 className="text-section-header font-semibold heading-tight text-text-primary">
            TrustLens
          </h1>
        </div>
        <a
          href="/"
          className="text-caption text-accent-blue hover:underline transition-colors duration-150"
        >
          ← নতুন বিশ্লেষণ
        </a>
      </header>

      {/* Loading state */}
      {isAnalyzing && (
        <ScanAnimation status={analysisStatus} />
      )}

      {/* Error state */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-trust-low/10 border border-trust-low/20"
        >
          <p className="text-body text-trust-low">{error}</p>
        </motion.div>
      )}

      {/* Results */}
      {result && !isAnalyzing && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col gap-12"
        >
          {/* Score + Radar row */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div className="flex justify-center">
              <TrustGauge score={result.trust_score} />
            </div>
            <div className="flex justify-center">
              <RadarChart
                pillars={result.pillars.map((p) => ({
                  name: p.name,
                  score: p.score,
                }))}
              />
            </div>
          </section>

          {/* Pillar cards grid */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-grid">
            {result.pillars.map((pillar, index) => (
              <PillarCard
                key={pillar.name}
                name={pillar.name}
                nameBn={pillar.name_bn}
                score={pillar.score}
                explanation={pillar.explanation_en}
                explanationBn={pillar.explanation_bn}
                evidence={pillar.evidence}
                active={pillar.active}
                index={index}
              />
            ))}
          </section>

          {/* Explanation */}
          <section className="flex flex-col gap-4">
            <h2 className="text-section-header font-semibold heading-tight text-text-primary">
              বিশ্লেষণ
            </h2>
            <div className="card p-5 flex flex-col gap-3">
              <p className="text-body-bn font-bengali text-text-primary leading-relaxed">
                {result.explanation_bn}
              </p>
              <p className="text-body text-text-secondary">
                {result.explanation_en}
              </p>
            </div>
          </section>

          {/* Metadata */}
          <section className="flex items-center gap-4 text-caption text-text-tertiary">
            <span>Confidence: {Math.round(result.confidence * 100)}%</span>
            <span>•</span>
            <span>{result.processing_time_ms}ms</span>
            {result.cached && (
              <>
                <span>•</span>
                <span className="text-accent-blue">Cached</span>
              </>
            )}
          </section>
        </motion.div>
      )}

      {/* No result and not loading */}
      {!result && !isAnalyzing && !error && (
        <div className="flex flex-col items-center gap-4 py-16">
          <p className="text-body text-text-secondary">
            No analysis results yet.
          </p>
          <a href="/" className="text-body text-accent-blue hover:underline">
            Start a new analysis →
          </a>
        </div>
      )}
    </div>
  );
}
