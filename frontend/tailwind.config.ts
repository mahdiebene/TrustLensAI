import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          0: "var(--surface-0)",
          1: "var(--surface-1)",
          2: "var(--surface-2)",
          3: "var(--surface-3)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          tertiary: "var(--text-tertiary)",
        },
        trust: {
          high: "var(--trust-high)",
          medium: "var(--trust-medium)",
          low: "var(--trust-low)",
        },
        accent: {
          blue: "var(--accent-blue)",
        },
      },
      fontFamily: {
        sans: ["Inter", "Hind Siliguri", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        bengali: ["Hind Siliguri", "Noto Sans Bengali", "sans-serif"],
      },
      fontSize: {
        caption: ["12px", { lineHeight: "1.5" }],
        "secondary-label": ["13px", { lineHeight: "1.5" }],
        body: ["14px", { lineHeight: "1.6" }],
        "body-bn": ["16px", { lineHeight: "1.75" }],
        "section-header": ["18px", { lineHeight: "1.4" }],
        "page-section": ["24px", { lineHeight: "1.3" }],
        "page-title": ["32px", { lineHeight: "1.2" }],
        "hero-number": ["48px", { lineHeight: "1" }],
        "score-display": ["64px", { lineHeight: "1" }],
      },
      letterSpacing: {
        "heading-tight": "-0.02em",
        "score-tight": "-0.04em",
        "caps-wide": "0.05em",
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },
      maxWidth: {
        content: "1200px",
      },
      animation: {
        "fade-up": "fadeUp 0.3s cubic-bezier(0.22, 1, 0.36, 1)",
        scan: "scan 2s cubic-bezier(0.16, 1, 0.3, 1) infinite",
        "score-reveal": "scoreReveal 0.9s cubic-bezier(0.22, 1, 0.36, 1)",
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        scoreReveal: {
          "0%": { opacity: "0", transform: "scale(0.8)" },
          "70%": { transform: "scale(1.02)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
      },
      transitionTimingFunction: {
        "enter": "cubic-bezier(0.22, 1, 0.36, 1)",
        "exit": "cubic-bezier(0.55, 0, 1, 0.45)",
        "move": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
