"use client";

import { useStore } from "@/lib/store";
import { getStrings } from "@/lib/i18n";

/**
 * Hook to get localized strings based on current language.
 */
export function useI18n() {
  const language = useStore((s) => s.language);
  return getStrings(language);
}
