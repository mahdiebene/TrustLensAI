"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface PillarCardProps {
  name: string;
  nameBn: string;
  score: number;
  explanation: string;
  explanationBn: string;
  evidence: string[];
  active: boolean;
  index: number;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "var(--trust-high)";
  if (score >= 40) return "var(--trust-medium)";
  return "var(--trust-low)";
}

export function PillarCard({
  name,
  nameBn,
  score,
  explanation,
  explanationBn,
  evidence,
  active,
  index,
}: PillarCardProps) {
  const [expanded, setExpanded] = useState(false);
  const color = getScoreColor(score);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1], delay: index * 0.05 }}
      onClick={() => setExpanded(!expanded)}
      className={`
        relative cursor-pointer rounded-lg overflow-hidden
        bg-surface-1 border border-surface-3/40
        hover:bg-surface-2 transition-colors duration-150 ease-enter
      `}
    >
      {/* Left accent bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[3px]"
        style={{ backgroundColor: active ? color : "var(--surface-3)" }}
      />

      {/* Card content */}
      <div className="pl-5 pr-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-body text-text-secondary">{name}</span>
            <span className="text-caption text-text-tertiary font-bengali">{nameBn}</span>
          </div>
          <span
            className="font-mono text-page-section font-semibold score-tight"
            style={{ color: active ? color : "var(--text-tertiary)" }}
          >
            {Math.round(score)}
          </span>
        </div>

        {/* One-line finding */}
        {!expanded && (
          <p className="text-secondary-label text-text-secondary mt-2 truncate">
            {explanation}
          </p>
        )}

        {/* Expanded content */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              className="mt-3 flex flex-col gap-2 overflow-hidden"
            >
              <p className="text-body text-text-primary">{explanation}</p>
              <p className="text-body-bn text-text-secondary font-bengali">{explanationBn}</p>
              {evidence.length > 0 && (
                <div className="flex flex-col gap-1 mt-2">
                  <span className="text-caption text-text-tertiary caps-wide uppercase">
                    Evidence
                  </span>
                  {evidence.map((item, i) => (
                    <span key={i} className="text-caption text-text-secondary">
                      • {item}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Inactive overlay */}
      {!active && (
        <div className="absolute inset-0 bg-surface-0/50 flex items-center justify-center">
          <span className="text-caption text-text-tertiary">Pending</span>
        </div>
      )}
    </motion.div>
  );
}
