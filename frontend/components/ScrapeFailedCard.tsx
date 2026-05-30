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

  const canSubmit = !submitting && (text.trim().length > 0 || imageUrl.trim().length > 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      className="card p-4 md:p-5 flex flex-col gap-5 max-w-2xl mx-auto w-full"
    >
      {/* Headline row */}
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-lg bg-trust-low/10 border border-trust-low/30 flex items-center justify-center shrink-0">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-trust-low"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <h2 className="text-[17px] md:text-[18px] font-semibold heading-tight text-text-primary">
            {t.scrapeFailedTitle}
          </h2>
          <p className="text-[13px] md:text-[14px] text-text-secondary leading-relaxed">
            {reason}
          </p>
        </div>
      </div>

      {/* Original URL pill */}
      {originalUrl && (
        <div className="flex flex-col gap-1 -mt-1">
          <span className="text-[10.5px] tracking-wider uppercase text-text-tertiary font-medium">
            {t.originalUrlLabel}
          </span>
          <a
            href={originalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[12.5px] text-accent-blue hover:underline break-all"
          >
            {originalUrl}
          </a>
        </div>
      )}

      <div className="hr-soft" />

      {/* Hint */}
      <p className="text-[13.5px] md:text-[14px] font-bengali text-text-primary leading-[1.7]">
        {t.scrapeFailedHint}
      </p>

      {/* Text input */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] tracking-wider uppercase text-text-tertiary font-medium">
          {t.pasteTextLabel}
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t.pasteTextPlaceholder}
          rows={5}
          className="w-full p-3 rounded-lg bg-surface-1 border border-surface-3/40 text-[14px] font-bengali text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent-blue/60 focus:shadow-[0_0_0_3px_rgba(59,130,246,0.08)] transition-all duration-150 resize-y leading-[1.65]"
          disabled={submitting}
        />
      </div>

      {/* Image URL input */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] tracking-wider uppercase text-text-tertiary font-medium">
          {t.imageUrlLabel}
        </label>
        <input
          type="url"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
          placeholder={t.imageUrlPlaceholder}
          className="w-full px-3 py-2.5 rounded-lg bg-surface-1 border border-surface-3/40 text-[14px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent-blue/60 focus:shadow-[0_0_0_3px_rgba(59,130,246,0.08)] transition-all duration-150"
          disabled={submitting}
        />
      </div>

      {/* Local error */}
      {localError && (
        <p className="text-[12.5px] text-trust-low flex items-center gap-1.5">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-trust-low" />
          {localError}
        </p>
      )}

      {/* Action buttons — full-bleed on mobile, side-by-side on sm+ */}
      <div className="flex flex-col-reverse sm:flex-row gap-2.5 pt-1">
        <Link
          href="/"
          className="flex-1 h-11 rounded-lg flex items-center justify-center text-[13.5px] font-medium bg-surface-2 text-text-secondary hover:bg-surface-3/50 active:scale-[0.99] transition-all duration-150"
        >
          ← {t.backToHome}
        </Link>
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="flex-1 h-11 rounded-lg font-medium text-[13.5px] font-bengali bg-accent-blue text-white hover:bg-accent-blue/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-150 active:scale-[0.99] flex items-center justify-center gap-2"
        >
          {submitting && (
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
          )}
          {submitting ? t.analyzing : t.analyzeManual}
        </button>
      </div>
    </motion.div>
  );
}
