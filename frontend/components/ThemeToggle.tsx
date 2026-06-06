"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useStore } from "@/lib/store";

/**
 * Two-state theme toggle: light | dark. Defaults to light.
 * Legacy "system" values from older builds are migrated to "light" on mount.
 * Animated icon swap via framer-motion for a smooth, modern feel.
 */
export function ThemeToggle() {
  const { theme, setTheme } = useStore();
  const [mounted, setMounted] = useState(false);

  // Hydrate from localStorage once on mount.
  useEffect(() => {
    setMounted(true);
    try {
      const saved = localStorage.getItem("trustlens-theme");
      const next: "light" | "dark" =
        saved === "dark" || saved === "light" ? saved : "light";
      setTheme(next);
    } catch {
      setTheme("light");
    }
  }, [setTheme]);

  // Apply + persist whenever the theme changes.
  useEffect(() => {
    if (!mounted) return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    try {
      localStorage.setItem("trustlens-theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme, mounted]);

  if (!mounted) return null;

  const isDark = theme === "dark";
  const next: "light" | "dark" = isDark ? "light" : "dark";

  return (
    <motion.button
      onClick={() => setTheme(next)}
      whileTap={{ scale: 0.92 }}
      whileHover={{ scale: 1.04 }}
      transition={{ type: "spring", stiffness: 400, damping: 22 }}
      className="
        relative h-8 w-8 grid place-items-center rounded-lg
        bg-surface-2 text-text-secondary
        border border-surface-3/50
        hover:bg-surface-3/70 hover:text-text-primary
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue/40
        transition-colors duration-150
      "
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      <AnimatePresence mode="wait" initial={false}>
        {isDark ? (
          <motion.svg
            key="moon"
            initial={{ opacity: 0, rotate: -90, scale: 0.6 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: 90, scale: 0.6 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </motion.svg>
        ) : (
          <motion.svg
            key="sun"
            initial={{ opacity: 0, rotate: 90, scale: 0.6 }}
            animate={{ opacity: 1, rotate: 0, scale: 1 }}
            exit={{ opacity: 0, rotate: -90, scale: 0.6 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="4.2" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </motion.svg>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
