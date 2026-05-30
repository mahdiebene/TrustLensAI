"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useSearchParams } from "next/navigation";
import { TrustGauge } from "@/components/TrustGauge";
import { PillarCard } from "@/components/PillarCard";
import { RadarChart } from "@/components/RadarChart";
import { ScanAnimation } from "@/components/ScanAnimation";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ScrapeFailedCard } from "@/components/ScrapeFailedCard";
import { Logo } from "@/components/Logo";
import { useStore } from "@/lib/store";
import { useI18n } from "@/lib/useI18n";
import { analyzeContent } from "@/lib/api";
import { saveRecentScan } from "@/lib/recentScans";

export function ResultsContent() {
  const t = useI18n();
  const {
    result,
    setResult,
    isAnalyzing,
    setIsAnalyzing,
    analysisStatus,
    setAnalysisStatus,
    language,
    error: storeError,
    setError: setStoreError,
  } = useStore();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(storeError);

  // Sync store-level error (set by InputForm on submit failure) into local state
  useEffect(() => {
    if (storeError) {
      setError(storeError);
    }
  }, [storeError]);

  useEffect(() => {
    const content = searchParams.get("content");
    if (content && !result && !isAnalyzing) {
      runAnalysis(content);
    }
  }, [searchParams]);

  // Clear store error when leaving the page so a new attempt starts clean
  useEffect(() => {
    return () => {
      setStoreError(null);
    };
  }, [setStoreError]);

  async function runAnalysis(content: string) {
    setIsAnalyzing(true);
    setError(null);
    setStoreError(null);

    const statuses = [
      t.checkingSources,
      t.analyzingLanguage,
      t.crossReferencing,
      t.generatingScore,
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
      saveRecentScan(content, data);
    } catch (e: any) {
      setError(e.message || "Analysis failed");
    } finally {
      clearInterval(statusInterval);
      setIsAnalyzing(false);
      setAnalysisStatus("");
    }
  }

  return (
    <div className="flex flex-col gap-8 md:gap-10">
      <header className="sticky top-0 z-20 -mx-6 md:-mx-10 lg:-mx-16 px-6 md:px-10 lg:px-16 py-4 backdrop-blur-md bg-surface-0/80 border-b border-surface-3/50">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center shrink-0">
            <Logo size={28} showWordmark />
          </Link>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <LanguageToggle />
            <Link
              href="/"
              className="ml-2 px-3 py-2 rounded-xl text-caption text-accent-blue bg-accent-blue/10 hover:bg-accent-blue/15 transition-colors duration-150"
            >
              ← {t.newAnalysis}
            </Link>
          </div>
        </div>
      </header>

      {/* Loading state */}
      {isAnalyzing && (
        <div className="section-surface p-5 md:p-6">
          <ScanAnimation status={analysisStatus} />
        </div>
      )}

      {/* Error state */}
      {error && !isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="section-surface p-5 md:p-6 flex flex-col gap-4 border border-trust-low/30"
        >
          <div className="flex items-start gap-3">
            <div className="h-9 w-9 rounded-lg bg-trust-low/10 border border-trust-low/30 flex items-center justify-center shrink-0">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-trust-low">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <div className="flex flex-col gap-1.5 min-w-0 flex-1">
              <h3 className="text-body font-semibold text-text-primary">
                {language === "bn" ? "বিশ্লেষণ ব্যর্থ হয়েছে" : "Analysis failed"}
              </h3>
              <p className="text-body text-text-secondary break-words">{error}</p>
            </div>
          </div>
          <div className="flex flex-col-reverse sm:flex-row gap-2.5 pt-1">
            <Link
              href="/"
              className="inline-flex items-center justify-center px-4 py-2.5 rounded-xl text-body text-accent-blue bg-accent-blue/10 hover:bg-accent-blue/15 transition-colors duration-150"
            >
              ← {t.newAnalysis}
            </Link>
          </div>
        </motion.div>
      )}

      {/* Scrape-failure state — show a card asking for text/image */}
      {result && !isAnalyzing && result.scrape_failed && (
        <ScrapeFailedCard
          reasonEn={result.scrape_reason_en || result.explanation_en}
          reasonBn={result.scrape_reason_bn || result.explanation_bn}
          originalUrl={result.original_url || ""}
        />
      )}

      {/* Results */}
      {result && !isAnalyzing && !result.scrape_failed && (
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
              {t.explanation}
            </h2>
            <div className="card p-5 flex flex-col gap-3">
              <p className="text-body-bn font-bengali text-text-primary leading-relaxed">
                {language === "bn" ? result.explanation_bn : result.explanation_en}
              </p>
              {language === "bn" && (
                <p className="text-body text-text-secondary">
                  {result.explanation_en}
                </p>
              )}
            </div>
          </section>

          {/* Metadata */}
          <section className="flex items-center gap-4 text-caption text-text-tertiary">
            <span>{t.confidence}: {Math.round(result.confidence * 100)}%</span>
            <span>•</span>
            <span>{result.processing_time_ms}ms</span>
            {result.cached && (
              <>
                <span>•</span>
                <span className="text-accent-blue">{t.cached}</span>
              </>
            )}
          </section>
        </motion.div>
      )}

      {/* No result and not loading */}
      {!result && !isAnalyzing && !error && (
        <div className="section-surface flex flex-col items-center gap-4 py-16 px-6 text-center">
          <p className="text-body text-text-secondary">{t.noResults}</p>
          <Link href="/" className="text-body text-accent-blue hover:underline">
            {t.startAnalysis}
          </Link>
        </div>
      )}
    </div>
  );
}
