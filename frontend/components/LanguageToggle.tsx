"use client";

import { useStore } from "@/lib/store";

export function LanguageToggle() {
  const { language, setLanguage } = useStore();

  return (
    <button
      onClick={() => setLanguage(language === "bn" ? "en" : "bn")}
      className="
        px-2.5 py-1 rounded-md text-caption font-medium
        bg-surface-2 text-text-secondary
        hover:bg-surface-3 hover:text-text-primary
        transition-colors duration-150 ease-enter
        flex items-center gap-1.5
      "
      aria-label={`Switch to ${language === "bn" ? "English" : "বাংলা"}`}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="2" y1="12" x2="22" y2="12" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
      <span>{language === "bn" ? "EN" : "বাং"}</span>
    </button>
  );
}
