import type { Metadata, Viewport } from "next";
import { Inter, Hind_Siliguri, JetBrains_Mono } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const hindSiliguri = Hind_Siliguri({
  subsets: ["bengali", "latin"],
  weight: ["400", "500", "600"],
  variable: "--font-hind-siliguri",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

const siteUrl = "https://www.trustlensai.tech";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "TrustLens — Live Trust Check for Bengali Social Media",
  description:
    "AI-powered trust scoring for Bengali & English social posts. Six independent signals, explainable verdicts. গুজব চিনুন, সত্য জানুন।",
  applicationName: "TrustLens",
  keywords: [
    "TrustLens",
    "fact check",
    "misinformation",
    "Bengali",
    "Bangladesh",
    "trust score",
    "fake news detector",
    "গুজব",
    "ফ্যাক্ট চেক",
  ],
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
  alternates: {
    canonical: siteUrl,
  },

  openGraph: {
    title: "TrustLens — Live Trust Check",
    description:
      "AI-powered trust scoring for Bengali & English social posts. Six independent signals, explainable verdicts. গুজব চিনুন, সত্য জানুন।",
    url: siteUrl,
    siteName: "TrustLens",
    type: "website",
    locale: "bn_BD",
    // og image is auto-injected from app/opengraph-image.tsx (1200x630)
  },
  twitter: {
    card: "summary_large_image",
    title: "TrustLens — Live Trust Check",
    description:
      "Six-signal trust scoring for Bengali social media. Explainable, bilingual, fast.",
    // twitter image is auto-injected from app/twitter-image.tsx
  },
};

export const viewport: Viewport = {
  themeColor: "#0b0d10",
};


// Inline script to prevent flash of wrong theme.

// Default = light. Only "light" or "dark" is honored; legacy "system" values
// are migrated to light on next load.
const themeScript = `
(function() {
  try {
    var saved = localStorage.getItem('trustlens-theme');
    var theme = (saved === 'dark' || saved === 'light') ? saved : 'light';
    if (saved !== theme) localStorage.setItem('trustlens-theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
  } catch(e) {}
})();
`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="bn"
      className={`${inter.variable} ${hindSiliguri.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-surface-0 text-text-primary antialiased overflow-x-hidden">
        <main className="mx-auto max-w-content px-6 md:px-10 lg:px-16 py-6 md:py-8 overflow-x-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
