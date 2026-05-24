"use client";

import { useEffect, useState } from "react";
import { motion, useSpring } from "framer-motion";

interface TrustGaugeProps {
  score: number;
  size?: number;
}

function getScoreColor(score: number): string {
  if (score >= 80) return "var(--trust-high)";
  if (score >= 40) return "var(--trust-medium)";
  return "var(--trust-low)";
}

function getVerdict(score: number): { en: string; bn: string } {
  if (score >= 80) return { en: "Highly Trustworthy", bn: "অত্যন্ত বিশ্বাসযোগ্য" };
  if (score >= 60) return { en: "Generally Reliable", bn: "সাধারণত নির্ভরযোগ্য" };
  if (score >= 40) return { en: "Questionable", bn: "সন্দেহজনক" };
  if (score >= 20) return { en: "Likely Unreliable", bn: "সম্ভবত অবিশ্বাসযোগ্য" };
  return { en: "High Risk", bn: "উচ্চ ঝুঁকি" };
}

export function TrustGauge({ score, size = 240 }: TrustGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0);

  const springValue = useSpring(0, { stiffness: 100, damping: 15, mass: 0.5 });

  useEffect(() => {
    springValue.set(score);
  }, [score, springValue]);

  useEffect(() => {
    const unsubscribe = springValue.on("change", (v) => {
      setDisplayScore(Math.round(v));
    });
    return unsubscribe;
  }, [springValue]);

  const color = getScoreColor(score);
  const verdict = getVerdict(score);
  const strokeWidth = size > 200 ? 12 : 8;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius * (270 / 360);
  const offset = circumference - (score / 100) * circumference;

  // Arc path for 270 degrees (open at bottom)
  const cx = size / 2;
  const cy = size / 2;

  return (
    <motion.div
      className="flex flex-col items-center gap-3"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="relative" style={{ width: size, height: size }}>
        {/* Glow */}
        <div
          className="absolute inset-0 rounded-full blur-2xl opacity-10"
          style={{ backgroundColor: color, transform: "scale(1.2)" }}
        />

        <svg width={size} height={size} className="rotate-[135deg]">
          {/* Background ring */}
          <circle
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke="var(--surface-3)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${2 * Math.PI * radius}`}
            opacity={0.3}
          />
          {/* Active ring */}
          <motion.circle
            cx={cx}
            cy={cy}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${2 * Math.PI * radius}`}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay: 0.2 }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono font-bold score-tight"
            style={{ fontSize: size > 200 ? "64px" : "48px", color }}
          >
            {displayScore}
          </span>
          <span className="text-body text-text-secondary">/ 100</span>
        </div>
      </div>

      {/* Verdict badge */}
      <div
        className="px-3 py-1 rounded-md text-caption font-medium"
        style={{ backgroundColor: `${color}15`, color }}
      >
        {verdict.en}
      </div>
    </motion.div>
  );
}
