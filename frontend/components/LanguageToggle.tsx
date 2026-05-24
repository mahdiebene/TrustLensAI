"use client";

import { useStore } from "@/lib/store";

export function LanguageToggle() {
  const { language, setLanguage } = useStore();

  return (
    <button
      onClick={() => setLanguage(language === "bn" ? "en" : "bn")}
      className="
        px-2 py-1 rounded text-caption font-medium
        bg-surface-2 text-text-secondary
        hover:bg-surface-3 transition-colors duration-150 ease-enter
      "
      aria-label="Toggle language"
    >
      {language === "bn" ? "বাং" : "EN"}
    </button>
  );
}
