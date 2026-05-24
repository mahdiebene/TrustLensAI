"use client";

import { motion } from "framer-motion";

interface RadarChartProps {
  pillars: Array<{
    name: string;
    score: number;
  }>;
  size?: number;
}

export function RadarChart({ pillars, size = 300 }: RadarChartProps) {
  // TODO: Phase 2H — Full hexagonal SVG radar chart with clockwise draw animation
  // For now, render a placeholder that shows the structure

  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.4;
  const angleStep = (2 * Math.PI) / 6;

  // Calculate points for the hexagonal grid
  const gridPoints = Array.from({ length: 6 }, (_, i) => {
    const angle = angleStep * i - Math.PI / 2;
    return {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });

  // Calculate data points based on scores
  const dataPoints = pillars.slice(0, 6).map((p, i) => {
    const angle = angleStep * i - Math.PI / 2;
    const r = (p.score / 100) * radius;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });

  const dataPath = dataPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";
  const gridPath = gridPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
    >
      <svg width={size} height={size}>
        {/* Grid hexagon */}
        <path d={gridPath} fill="none" stroke="var(--surface-3)" strokeWidth={1} opacity={0.4} />

        {/* Axis lines */}
        {gridPoints.map((p, i) => (
          <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="var(--surface-3)" strokeWidth={1} opacity={0.2} />
        ))}

        {/* Data polygon */}
        {pillars.length >= 6 && (
          <motion.path
            d={dataPath}
            fill="var(--accent-blue)"
            fillOpacity={0.1}
            stroke="var(--accent-blue)"
            strokeWidth={2}
            initial={{ pathLength: 0, fillOpacity: 0 }}
            animate={{ pathLength: 1, fillOpacity: 0.1 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          />
        )}

        {/* Axis labels */}
        {pillars.slice(0, 6).map((p, i) => {
          const angle = angleStep * i - Math.PI / 2;
          const labelR = radius + 20;
          const lx = cx + labelR * Math.cos(angle);
          const ly = cy + labelR * Math.sin(angle);
          return (
            <text
              key={i}
              x={lx}
              y={ly}
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-caption"
              fill="var(--text-secondary)"
              fontSize={11}
            >
              {p.name}
            </text>
          );
        })}
      </svg>
    </motion.div>
  );
}
