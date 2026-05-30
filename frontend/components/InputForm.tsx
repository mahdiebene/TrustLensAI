"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useStore } from "@/lib/store";
import { useI18n } from "@/lib/useI18n";
import { analyzeContent } from "@/lib/api";
import { saveRecentScan } from "@/lib/recentScans";

export function InputForm() {
  const router = useRouter();
  const t = useI18n();
  const { setResult, setIsAnalyzing, setAnalysisStatus, language } = useStore();
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [detectedLang, setDetectedLang] = useState<"BN" | "EN" | "Mixed" | null>(null);
  const [urlDetected, setUrlDetected] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);

  // Simple language detection based on character ranges
  const detectLanguage = useCallback((text: string) => {
    if (!text.trim()) {
      setDetectedLang(null);
      return;
    }
    const bengaliChars = text.match(/[\u0980-\u09FF]/g)?.length || 0;
    const latinChars = text.match(/[a-zA-Z]/g)?.length || 0;
    const total = bengaliChars + latinChars;

    if (total === 0) {
      setDetectedLang(null);
    } else if (bengaliChars > total * 0.7) {
      setDetectedLang("BN");
    } else if (latinChars > total * 0.7) {
      setDetectedLang("EN");
    } else {
      setDetectedLang("Mixed");
    }
  }, []);

  // URL detection
  const detectUrl = useCallback((text: string) => {
    const urlPattern = /https?:\/\/[^\s]+/;
    setUrlDetected(urlPattern.test(text));
  }, []);

  const handleInput = useCallback(() => {
    const text = editorRef.current?.innerText || "";
    setContent(text);
    detectLanguage(text);
    detectUrl(text);
  }, [detectLanguage, detectUrl]);

  const handleSubmit = async () => {
    if (!content.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setIsAnalyzing(true);
    setResult(null);

    const statuses = [
      t.checkingSources,
      t.analyzingLanguage,
      t.crossReferencing,
      t.generatingScore,
    ];

    let statusIndex = 0;
    setAnalysisStatus(statuses[0]);

    const statusInterval = setInterval(() => {
      statusIndex = (statusIndex + 1) % statuses.length;
      setAnalysisStatus(statuses[statusIndex]);
    }, 2500);

    try {
      const data = await analyzeContent({ content: content.trim() });
      setResult(data);
      saveRecentScan(content.trim(), data);
      clearInterval(statusInterval);
      setIsAnalyzing(false);
      router.push("/results");
    } catch (error: any) {
      clearInterval(statusInterval);
      setIsAnalyzing(false);
      console.error("Analysis failed:", error);
      router.push("/results");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Content-editable input area */}
      <div className="relative">
        <div
          ref={editorRef}
          contentEditable
          onInput={handleInput}
          className={`
            min-h-[120px] p-4 rounded-lg
            bg-surface-1 border border-surface-3/40
            text-body-bn text-text-primary font-bengali
            focus:outline-none focus:border-accent-blue focus:shadow-[0_0_0_3px_rgba(59,130,246,0.1)]
            transition-all duration-200 ease-enter
            ${isSubmitting ? "opacity-50 pointer-events-none" : ""}
            empty:before:content-[attr(data-placeholder)] empty:before:text-text-tertiary
          `}
          data-placeholder={t.placeholder}
          role="textbox"
          aria-label="Content to analyze"
        />

        {/* Language indicator pill */}
        {detectedLang && (
          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute top-3 right-3 px-2 py-0.5 rounded text-caption font-medium bg-surface-2 text-text-secondary"
          >
            {detectedLang}
          </motion.span>
        )}

        {/* URL detected chip */}
        {urlDetected && (
          <motion.span
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-3 left-4 px-2 py-0.5 rounded text-caption bg-accent-blue/10 text-accent-blue"
          >
            {t.urlDetected}
          </motion.span>
        )}

        {/* Scan animation overlay */}
        {isSubmitting && (
          <div className="absolute inset-0 overflow-hidden rounded-lg pointer-events-none">
            <motion.div
              className="absolute left-0 right-0 h-px bg-accent-blue/60"
              animate={{ top: ["0%", "100%"] }}
              transition={{ duration: 2, repeat: Infinity, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
        )}
      </div>

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={!content.trim() || isSubmitting}
        className={`
          w-full py-3 rounded-lg font-medium text-body-bn
          bg-accent-blue text-white
          hover:bg-accent-blue/90
          disabled:opacity-40 disabled:cursor-not-allowed
          transition-all duration-150 ease-enter
          active:scale-[0.99]
        `}
      >
        {isSubmitting ? t.analyzing : t.analyze}
      </button>

      {/* Progress text during analysis */}
      {isSubmitting && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-caption text-text-secondary text-center"
        >
          {useStore.getState().analysisStatus}
        </motion.p>
      )}
    </div>
  );
}
