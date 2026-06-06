"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/useI18n";

/**
 * Mobile-first bottom navigation. Hidden on md+. Frosted glass per design skill.
 * Anchors to the four primary sections of the home page.
 */
export function MobileBottomNav() {
  const t = useI18n();
  const [active, setActive] = useState<string>("verify");

  useEffect(() => {
    const ids = ["verify", "how", "tools", "scans"];
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActive(entry.target.id);
            break;
          }
        }
      },
      { threshold: 0.4, rootMargin: "-30% 0px -50% 0px" }
    );
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  const items = [
    { id: "verify", label: t.verifyContent, icon: <IconVerify /> },
    { id: "how", label: t.howItWorks, icon: <IconHow /> },
    { id: "tools", label: t.botExtension, icon: <IconTools /> },
    { id: "scans", label: t.recentScanned, icon: <IconHistory /> },
  ];

  return (
    <nav
      className="md:hidden fixed inset-x-0 bottom-0 z-30 pb-safe pt-2 px-3 backdrop-blur-xl bg-surface-0/85 border-t border-surface-3/60"
      aria-label="Mobile navigation"
    >
      <ul className="flex items-stretch justify-between gap-1">
        {items.map((item) => {
          const isActive = active === item.id;
          return (
            <li key={item.id} className="flex-1">
              <motion.a
                href={`#${item.id}`}
                whileTap={{ scale: 0.92 }}
                transition={{ type: "spring", stiffness: 380, damping: 26 }}
                className={`relative flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-xl transition-colors duration-150 ${
                  isActive ? "text-accent-blue" : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {isActive && (
                  <motion.span
                    layoutId="bottomNavActive"
                    className="absolute inset-0 rounded-xl bg-accent-blue/10"
                    transition={{ type: "spring", stiffness: 360, damping: 30 }}
                  />
                )}
                <span className="relative h-5 w-5">{item.icon}</span>
                <span className="relative text-[10px] leading-none font-medium tracking-[-0.005em] truncate max-w-full">
                  {item.label}
                </span>
              </motion.a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

/* ---------- Icons (24px, single-stroke, follow design skill) ---------- */

function IconVerify() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3 L20 6 V12 C20 16 16.5 19.5 12 21 C7.5 19.5 4 16 4 12 V6 Z" />
      <path d="M9 12 L11 14 L15 10" />
    </svg>
  );
}

function IconHow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9 A2.5 2.5 0 0 1 14.5 9 C14.5 11 12 11 12 13" />
      <line x1="12" y1="16.5" x2="12.01" y2="16.5" />
    </svg>
  );
}

function IconTools() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="14" rx="2" />
      <path d="M8 22 H16" />
      <path d="M12 18 V22" />
    </svg>
  );
}

function IconHistory() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12 A9 9 0 1 0 6 5.5" />
      <polyline points="3 4 3 10 9 10" />
      <path d="M12 8 V12 L15 14" />
    </svg>
  );
}
