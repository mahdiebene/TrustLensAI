"use client";

import { useCallback, useRef, useState } from "react";
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
  const [imageDataUrl, setImageDataUrl] = useState<string>("");
  const [imageFileName, setImageFileName] = useState<string>("");
  const [imageError, setImageError] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reason = language === "bn" ? reasonBn : reasonEn;

  // Mirror the InputForm upload flow: read file -> downscale to <=1280px JPEG
  // to stay under Vercel's 4.5MB serverless body limit, then send as a data URL.
  const handleFile = useCallback(
    (file: File | undefined) => {
      setImageError("");
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        setImageError(t.imageInvalidType);
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setImageError(t.imageTooLarge);
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const original = typeof reader.result === "string" ? reader.result : "";
        if (!original) {
          setImageError(t.imageReadFailed);
          return;
        }
        const img = new Image();
        img.onload = () => {
          try {
            const maxDim = 1280;
            let { width, height } = img;
            if (width > maxDim || height > maxDim) {
              const ratio = Math.min(maxDim / width, maxDim / height);
              width = Math.round(width * ratio);
              height = Math.round(height * ratio);
            }
            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext("2d");
            if (!ctx) {
              setImageDataUrl(original);
              setImageFileName(file.name);
              return;
            }
            ctx.drawImage(img, 0, 0, width, height);
            const compressed = canvas.toDataURL("image/jpeg", 0.82);
            setImageDataUrl(compressed.length < original.length ? compressed : original);
            setImageFileName(file.name);
          } catch {
            setImageDataUrl(original);
            setImageFileName(file.name);
          }
        };
        img.onerror = () => setImageError(t.imageReadFailed);
        img.src = original;
      };
      reader.onerror = () => setImageError(t.imageReadFailed);
      reader.readAsDataURL(file);
    },
    [t]
  );

  const removeImage = () => {
    setImageDataUrl("");
    setImageFileName("");
    setImageError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async () => {
    const trimmed = text.trim();
    if (!trimmed && !imageDataUrl) return;

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
        image_url: imageDataUrl || undefined,
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

  const canSubmit = !submitting && (text.trim().length > 0 || imageDataUrl.length > 0);

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

      {/* Image upload (replaces the old paste-a-URL field) */}
      <div className="flex flex-col gap-1.5">
        <label className="text-[11px] tracking-wider uppercase text-text-tertiary font-medium">
          {t.imageUploadLabel}
        </label>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="sr-only"
          onChange={(e) => handleFile(e.target.files?.[0])}
          disabled={submitting}
        />

        {!imageDataUrl ? (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={submitting}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              handleFile(e.dataTransfer.files?.[0]);
            }}
            className="w-full flex flex-col items-center justify-center gap-1.5 py-6 px-3 rounded-lg bg-surface-1 border border-dashed border-surface-3/50 hover:border-accent-blue/50 hover:bg-surface-2/40 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-text-tertiary"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <span className="text-[13.5px] text-text-secondary">{t.imageUploadCta}</span>
            <span className="text-[11.5px] text-text-tertiary">{t.imageUploadHint}</span>
          </button>
        ) : (
          <div className="flex items-center gap-3 p-2.5 rounded-lg bg-surface-1 border border-surface-3/40">
            <img
              src={imageDataUrl}
              alt="upload preview"
              className="h-12 w-12 rounded-md object-cover shrink-0"
            />
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-[13px] text-text-primary truncate">{imageFileName}</span>
              <span className="text-[11.5px] text-text-tertiary">{t.imageReady}</span>
            </div>
            <button
              type="button"
              onClick={removeImage}
              disabled={submitting}
              className="text-[12px] text-text-secondary hover:text-trust-low transition-colors px-2 py-1 disabled:opacity-40"
            >
              {t.remove}
            </button>
          </div>
        )}

        {imageError && (
          <p className="text-[12px] text-trust-low flex items-center gap-1.5">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-trust-low" />
            {imageError}
          </p>
        )}
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
