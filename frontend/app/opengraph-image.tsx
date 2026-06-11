import { ImageResponse } from "next/og";

// Route segment config
export const runtime = "edge";
export const alt = "TrustLens — Live Trust Check for Bengali Social Media";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Dynamically generated 1200x630 social preview (Open Graph / Twitter card).
export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background:
            "linear-gradient(135deg, #0b0d10 0%, #0f1422 55%, #0b1a2e 100%)",
          padding: "72px 80px",
          fontFamily: "Inter, sans-serif",
          color: "#ffffff",
          position: "relative",
        }}
      >
        {/* soft glow accent */}
        <div
          style={{
            position: "absolute",
            top: -160,
            right: -120,
            width: 520,
            height: 520,
            borderRadius: 9999,
            background:
              "radial-gradient(circle, rgba(59,130,246,0.35) 0%, rgba(59,130,246,0) 70%)",
            display: "flex",
          }}
        />

        {/* Brand row */}
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div
            style={{
              width: 88,
              height: 88,
              borderRadius: 20,
              background: "#0F0F12",
              border: "2px solid rgba(59,130,246,0.6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="56" height="56" viewBox="0 0 32 32" fill="none">
              <path
                d="M16 5 L25 8.2 V15 C25 20.2 21.4 24.2 16 26.5 C10.6 24.2 7 20.2 7 15 V8.2 Z"
                stroke="#3b82f6"
                strokeWidth="1.8"
                strokeLinejoin="round"
                fill="none"
              />
              <circle
                cx="14.5"
                cy="14"
                r="3.6"
                stroke="#3b82f6"
                strokeWidth="1.8"
                fill="none"
              />
              <path
                d="M17.2 16.5 L20.5 19.8"
                stroke="#3b82f6"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 46, fontWeight: 700, letterSpacing: -1 }}>
              TrustLens
            </div>
            <div style={{ fontSize: 24, color: "#93c5fd", fontWeight: 500 }}>
              trustlensai.tech
            </div>
          </div>
        </div>

        {/* Headline */}
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div
            style={{
              fontSize: 64,
              fontWeight: 800,
              lineHeight: 1.1,
              letterSpacing: -1.5,
              maxWidth: 980,
            }}
          >
            Live Trust Check for Bengali Social Media
          </div>
          <div
            style={{
              fontSize: 30,
              color: "#cbd5e1",
              fontWeight: 400,
              maxWidth: 900,
            }}
          >
            AI-powered trust scoring with six independent signals — explainable,
            bilingual verdicts.
          </div>
        </div>

        {/* Footer pills */}
        <div style={{ display: "flex", gap: 16 }}>
          {["AI Verifier", "6 Signals", "বাংলা + English"].map((t) => (
            <div
              key={t}
              style={{
                display: "flex",
                fontSize: 24,
                fontWeight: 600,
                color: "#bfdbfe",
                background: "rgba(59,130,246,0.15)",
                border: "1px solid rgba(59,130,246,0.4)",
                borderRadius: 9999,
                padding: "12px 28px",
              }}
            >
              {t}
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size }
  );
}
