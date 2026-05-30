"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useI18n } from "@/lib/useI18n";
import { useStore } from "@/lib/store";
import { analyzeContent } from "@/lib/api";
import { saveRecentScan } from "@/lib/recentScans";

interface ScrapeFailedCardProps {
  reasonEn: string;
  reasonBn: string;
  originalUrl: string;
}

export function ScrapeFailedCard({ reasonEn, reasonBn, originalUrl }: ScrapeFailedCardProps) {
  const t = useI18n();
  const { language, setResult, setIsAnalyzing, setAnalysisStatus } = useStore();
  const [text, setText] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const reason = language === "bn" ? reasonBn : reasonEn;

  const handleSubmit = async () => {
    const trimmed = text.trim();
    if (!trimmed && !imageUrl.trim()) return;

    setSubmitting(true);
    setLocalError(null);
    setIsAnalyzing(true);
    setAnalysisStatus(t.checkingSources);

    // Build content: include the original URL as context for the AI
    const content = trimmed
      ? `Original URL: ${originalUrl}\n\nUser-provided post text:\n${trimmed}`
      : `Original URL: ${originalUrl}\n\n(No text provided — analyze the screenshot/image.)`;

    try {
      const data = await analyzeContent({
        content,
        image_url: imageUrl.trim() || undefined,
      });
      setResult(data);
      saveRecentScan(originalUrl, data);
    } catch (e: any) {
      setLocalError(e?.message || "Analysis failed");
    } finally {
      setIsAnalyzing(false);
      setAnalysisStatus("");
      setSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="section-surface p-6 md:p-8 flex flex-col gap-6 max-w-2xl mx-auto w-full"
    >
      {/* Icon + headline */}
      <div className="flex items-start gap-4">
        <div className="h-12 w-12 rounded-2xl bg-trust-low/10 border border-trust-low/30 flex items-center justify-center shrink-0">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-trust-low"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <div className="flex flex-col gap-1.5">
          <h2 className="text-section-header font-semibold heading-tight text-text-primary">
            {t.scrapeFailedTitle}
          </h2>
          <p className="text-body text-text-secondary leading-relaxed">{reason}</p>
        </div>
      </div>

      {/* Original URL pill */}
      {originalUrl && (
        <div className="flex flex-col gap-1">
          <span className="text-caption text-text-tertiary uppercase caps-wide">
            {t.originalUrlLabel}
          </span>
          <a
            href={originalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-caption text-accent-blue hover:underline break-all"
          >
            {originalUrl}
          </a>
        </div>
      )}

      {/* Hint */}
      <p className="text-body-bn font-bengali text-text-primary leading-relaxed">
        {t.scrapeFailedHint}
      </p>

      {/* Text input */}
      <div className="flex flex-col gap-2">
        <label className="text-caption text-text-secondary font-medium">
          {t.pasteTextLabel}
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t.pasteTextPlaceholder}
          rows={6}
          className="w-full p-4 rounded-lg bg-surface-1 border border-surface-3/40 text-body-bn font-bengali text-text-primary focus:outline-none focus:border-accent-blue focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] transition-all duration-200 resize-y"
          disabled={submitting}
        />
      </div>

      {/* Image URL input */}
      <div className="flex flex-col gap-2">
        <label className="text-caption text-text-secondary font-medium">
          {t.imageUrlLabel}
        </label>
        <input
          type="url"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          placeholder={t.imageUrlPlaceholder}
          className="w-full p-3 rounded-lg bg-surface-1 border border-surface-3/40 text-body text-text-primary focus:outline-none focus:border-accent-blue focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] transition-all duration-200"
          disabled={submitting}
        />
      </div>

      {/* Local error */}
      {localError && (
        <p className="text-caption text-trust-low">{localError}</p>
      )}

      {/* Action buttons */}
      <div className="flex flex-col-reverse sm:flex-row gap-3">
        <Link
          href="/"
          className="flex-1 py-3 px-5 rounded-lg text-center font-medium text-body bg-surface-2 text-text-secondary hover:bg-surface-3/50 transition-colors duration-150"
        >
          ← {t.backToHome}
        </Link>
        <button
          onClick={handleSubmit}
          disabled={submitting || (!text.trim() && !imageUrl.trim())}
          className="flex-1 py-3 px-5 rounded-lg font-medium text-body-bn bg-accent-blue text-white hover:bg-accent-blue/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 active:scale-[0.99]"
        >
          {submitting ? t.analyzing : t.analyzeManual}
        </button>
      </div>
    </motion.div>
  );
}
