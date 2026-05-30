"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useStore } from "@/lib/store";
import { useI18n } from "@/lib/useI18n";
import { analyzeContent } from "@/lib/api";
import { saveRecentScan } from "@/lib/recentScans";

type InputMode = "auto" | "text" | "image";

const URL_REGEX = /https?:\/\/[^\s]+/i;

export function InputForm() {
  const router = useRouter();
  const t = useI18n();
  const { setResult, setIsAnalyzing, setAnalysisStatus, language } = useStore();

  const [mode, setMode] = useState<InputMode>("auto");
  const [text, setText] = useState("");
  const [imageDataUrl, setImageDataUrl] = useState<string>("");
  const [imageFileName, setImageFileName] = useState<string>("");
  const [imageError, setImageError] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [statusText, setStatusText] = useState("");

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Detection (Bengali / English / Mixed) + URL chip
  const detection = useMemo_detection(text);

  const canSubmit =
    !submitting &&
    ((mode === "image" && imageDataUrl.length > 0) ||
      (mode !== "image" && text.trim().length > 0));

  const handleFile = useCallback((file: File | null | undefined) => {
    setImageError("");
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setImageError(t.imageInvalidType);
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setImageError(t.imageTooLarge);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setImageDataUrl(typeof reader.result === "string" ? reader.result : "");
      setImageFileName(file.name);
    };
    reader.onerror = () => setImageError(t.imageReadFailed);
    reader.readAsDataURL(file);
  }, [t]);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setIsAnalyzing(true);
    setResult(null);

    const statuses = [t.checkingSources, t.analyzingLanguage, t.crossReferencing, t.generatingScore];
    let i = 0;
    setStatusText(statuses[0]);
    setAnalysisStatus(statuses[0]);
    const timer = setInterval(() => {
      i = (i + 1) % statuses.length;
      setStatusText(statuses[i]);
      setAnalysisStatus(statuses[i]);
    }, 2200);

    try {
      const payload =
        mode === "image"
          ? {
              content: text.trim() || imageFileName || "(image upload)",
              image_url: imageDataUrl || undefined,
            }
          : { content: text.trim() };
      const data = await analyzeContent(payload);
      setResult(data);
      saveRecentScan(payload.content, data);
      router.push("/results");
    } catch (e) {
      console.error("Analysis failed:", e);
      router.push("/results");
    } finally {
      clearInterval(timer);
      setIsAnalyzing(false);
      setSubmitting(false);
      setStatusText("");
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 240)}px`;
  }, [text]);

  // Pick the right placeholder per mode
  const placeholder =
    mode === "image"
      ? t.imageModeHint
      : detection.isUrl
      ? t.urlModeHint
      : t.placeholder;

  return (
    <div className="flex flex-col gap-3">
      {/* Mode tabs */}
      <div role="tablist" aria-label={t.inputMode} className="flex items-center gap-1 p-1 rounded-xl bg-surface-2/70 border border-surface-3/50 self-start">
        <ModeTab active={mode === "auto"} onClick={() => setMode("auto")} label={t.modeAuto} />
        <ModeTab active={mode === "text"} onClick={() => setMode("text")} label={t.modeText} />
        <ModeTab active={mode === "image"} onClick={() => setMode("image")} label={t.modeImage} />
      </div>

      {/* Primary text input — always visible (URL or post text) */}
      <div className="relative group">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          rows={3}
          spellCheck={false}
          disabled={submitting}
          className="w-full resize-none px-4 py-3.5 pr-14 rounded-xl bg-surface-1 border border-surface-3/60 text-[15px] leading-[1.7] text-text-primary placeholder:text-text-tertiary font-bengali focus:outline-none focus:border-accent-blue focus:shadow-[0_0_0_3px_rgba(59,130,246,0.12)] transition-all duration-150 min-h-[96px] disabled:opacity-50"
        />

        {/* Detection chip (top-right) */}
        <AnimatePresence>
          {(detection.isUrl || detection.lang) && !submitting && (
            <motion.span
              key={detection.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className={`absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md text-[11px] font-medium tracking-[0.04em] ${
                detection.isUrl
                  ? "bg-accent-blue/12 text-accent-blue"
                  : "bg-surface-3/60 text-text-secondary"
              }`}
            >
              {detection.label}
            </motion.span>
          )}
        </AnimatePresence>

        {/* Scan line during submit */}
        {submitting && (
          <div className="absolute inset-0 overflow-hidden rounded-xl pointer-events-none">
            <motion.div
              className="absolute left-0 right-0 h-px bg-accent-blue/70 shadow-[0_0_8px_2px_rgba(59,130,246,0.4)]"
              initial={{ top: "0%" }}
              animate={{ top: "100%" }}
              transition={{ duration: 1.6, repeat: Infinity, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
        )}
      </div>

      {/* Image upload — only when image mode */}
      <AnimatePresence initial={false}>
        {mode === "image" && (
          <motion.div
            key="image-input"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="flex flex-col gap-1.5">
              <label className="text-[11px] uppercase tracking-[0.06em] text-text-tertiary">
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
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleFile(e.dataTransfer.files?.[0]);
                  }}
                  disabled={submitting}
                  className="w-full flex flex-col items-center justify-center gap-2 px-4 py-6 rounded-xl bg-surface-1 border border-dashed border-surface-3/70 hover:border-accent-blue/60 hover:bg-accent-blue/[0.03] focus:outline-none focus:border-accent-blue focus:shadow-[0_0_0_3px_rgba(59,130,246,0.12)] transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="text-text-tertiary">
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <circle cx="9" cy="9" r="1.5" />
                    <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
                  </svg>
                  <span className="text-[13.5px] text-text-secondary">{t.imageUploadCta}</span>
                  <span className="text-[11.5px] text-text-tertiary">{t.imageUploadHint}</span>
                </button>
              ) : (
                <div className="relative flex items-center gap-3 px-3 py-2.5 rounded-xl bg-surface-1 border border-surface-3/60">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={imageDataUrl}
                    alt="upload preview"
                    className="h-12 w-12 rounded-md object-cover border border-surface-3/40 shrink-0"
                  />
                  <div className="flex flex-col min-w-0 flex-1">
                    <span className="text-[13px] text-text-primary truncate">{imageFileName}</span>
                    <span className="text-[11.5px] text-text-tertiary">{t.imageReady}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setImageDataUrl("");
                      setImageFileName("");
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                    disabled={submitting}
                    className="px-2.5 py-1 rounded-md text-[12px] text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors duration-150"
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
              <p className="text-[12px] text-text-tertiary">{t.imageModeHelp}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Submit row */}
      <div className="flex items-center gap-3 pt-1">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="flex-1 sm:flex-initial sm:px-7 py-3 rounded-xl font-medium text-[14px] tracking-[-0.005em] bg-accent-blue text-white shadow-[0_1px_2px_rgba(15,23,42,0.08)] hover:bg-[color-mix(in_srgb,var(--accent-blue)_92%,white)] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-accent-blue transition-all duration-150 active:scale-[0.99] flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <Spinner />
              <span className="font-bengali">{t.analyzing}</span>
            </>
          ) : (
            <span className="font-bengali">{t.verifyTrustworthiness}</span>
          )}
        </button>

        {!submitting && (text || imageDataUrl) && (
          <button
            type="button"
            onClick={() => {
              setText("");
              setImageDataUrl("");
              setImageFileName("");
              setImageError("");
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
            className="px-3.5 py-3 rounded-xl text-[13px] text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors duration-150"
          >
            {t.clear}
          </button>
        )}
      </div>

      {/* Live status during submit */}
      <AnimatePresence>
        {submitting && statusText && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="flex items-center gap-2 text-[12px] text-text-secondary"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-accent-blue animate-pulse" />
            <span>{statusText}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* --------------------------- helpers --------------------------- */

function ModeTab({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`relative px-3 py-1.5 rounded-lg text-[12px] font-medium tracking-[-0.005em] transition-colors duration-150 ${
        active ? "text-text-primary" : "text-text-secondary hover:text-text-primary"
      }`}
    >
      {active && (
        <motion.span
          layoutId="modeTabBg"
          className="absolute inset-0 rounded-lg bg-surface-1 border border-surface-3/60 shadow-[0_1px_2px_rgba(15,23,42,0.04)]"
          transition={{ type: "spring", stiffness: 380, damping: 30 }}
        />
      )}
      <span className="relative">{label}</span>
    </button>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4 text-white/90" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="42 14" />
    </svg>
  );
}

/**
 * Lightweight detection — kept inline so the form has zero deps.
 * Returns:
 *   { isUrl: boolean, lang: 'BN' | 'EN' | 'MIXED' | null, label: string }
 */
function useMemo_detection(text: string) {
  const trimmed = text.trim();
  if (!trimmed) return { isUrl: false, lang: null as null, label: "" };

  const isUrl = URL_REGEX.test(trimmed) && trimmed.split(/\s+/).length <= 2;

  const bn = trimmed.match(/[\u0980-\u09FF]/g)?.length || 0;
  const en = trimmed.match(/[A-Za-z]/g)?.length || 0;
  const total = bn + en;
  let lang: "BN" | "EN" | "MIXED" | null = null;
  if (total > 4) {
    if (bn / total > 0.7) lang = "BN";
    else if (en / total > 0.7) lang = "EN";
    else lang = "MIXED";
  }

  const label = isUrl ? "URL" : lang ?? "";
  return { isUrl, lang, label };
}
