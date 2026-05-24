"use client";

import { motion } from "framer-motion";

interface ScanAnimationProps {
  status: string;
}

export function ScanAnimation({ status }: ScanAnimationProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      {/* Scan line container */}
      <div className="relative w-full h-24 rounded-lg bg-surface-1 border border-surface-3/40 overflow-hidden">
        <motion.div
          className="absolute left-0 right-0 h-px bg-accent-blue/60"
          animate={{ top: ["0%", "100%"] }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: [0.16, 1, 0.3, 1],
          }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-caption text-text-secondary">{status}</span>
        </div>
      </div>
    </div>
  );
}
