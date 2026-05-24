"use client";

import { motion } from "framer-motion";

interface RadarChartProps {
  pillars: Array<{ name: string; score: number }>;
  size?: number;
}

const LABELS_BN: Record<string, string> = {
  "Source Reputation": "উৎস",
  "Content Consistency": "সামঞ্জস্য",
  "Language Analysis": "ভাষা",
  "Bengali Context": "প্রসঙ্গ",
  "Image Authenticity": "ছবি",
  "Author/Network": "লেখক",
};

export function RadarChart({ pillars, size = 280 }: RadarChartProps) {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.35;
  const levels = 4;
  const angleStep = (2 * Math.PI) / 6;

  // Grid hexagons
  const gridPaths = Array.from({ length: levels }, (_, level) => {
    const r = radius * ((level + 1) / levels);
    const pts = Array.from({ length: 6 }, (_, i) => {
      const a = angleStep * i - Math.PI / 2;
      return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`;
    });
    return pts.join(" ");
  });

  // Data polygon
  const dataPoints = pillars.slice(0, 6).map((p, i) => {
    const a = angleStep * i - Math.PI / 2;
    const r = (p.score / 100) * radius;
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
  });
  const dataPath = dataPoints.length === 6
    ? dataPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z"
    : "";

  // Axis endpoints
  const axes = Array.from({ length: 6 }, (_, i) => {
    const a = angleStep * i - Math.PI / 2;
    return { x: cx + radius * Math.cos(a), y: cy + radius * Math.sin(a) };
  });

  // Label positions (slightly beyond axes)
  const labelPos = Array.from({ length: 6 }, (_, i) => {
    const a = angleStep * i - Math.PI / 2;
    const lr = radius + 24;
    return { x: cx + lr * Math.cos(a), y: cy + lr * Math.sin(a) };
  });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
    >
      <svg width={size} height={size}>
        {/* Grid */}
        {gridPaths.map((pts, i) => (
          <polygon key={i} points={pts} fill="none" stroke="var(--surface-3)" strokeWidth={0.5} opacity={0.3} />
        ))}

        {/* Axes */}
        {axes.map((p, i) => (
          <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="var(--surface-3)" strokeWidth={0.5} opacity={0.25} />
        ))}

        {/* Data polygon — draws clockwise over 800ms */}
        {dataPath && (
          <>
            <motion.path
              d={dataPath}
              fill="var(--accent-blue)"
              fillOpacity={0}
              stroke="var(--accent-blue)"
              strokeWidth={2}
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.5 }}
            />
            <motion.path
              d={dataPath}
              fill="var(--accent-blue)"
              stroke="none"
              initial={{ fillOpacity: 0 }}
              animate={{ fillOpacity: 0.08 }}
              transition={{ duration: 0.2, delay: 1.1 }}
            />
          </>
        )}

        {/* Score dots */}
        {dataPoints.map((p, i) => (
          <motion.circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={3}
            fill="var(--accent-blue)"
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2, delay: 0.5 + i * 0.1 }}
          />
        ))}

        {/* Labels */}
        {pillars.slice(0, 6).map((p, i) => (
          <text
            key={i}
            x={labelPos[i].x}
            y={labelPos[i].y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="var(--text-secondary)"
            fontSize={11}
          >
            {LABELS_BN[p.name] || p.name.split(" ")[0]}
          </text>
        ))}
      </svg>
    </motion.div>
  );
}
