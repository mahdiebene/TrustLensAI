"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useStore } from "@/lib/store";

// Direct download of the packaged .zip build. Defaults to the copy bundled with
// the site (frontend/public/trustlens-extension.zip) — env can override if the
// build is ever hosted elsewhere (CDN / GitHub Release).
const EXTENSION_ZIP_URL =
  process.env.NEXT_PUBLIC_CHROME_EXTENSION_ZIP_URL || "/trustlens-extension.zip";
// Optional Chrome Web Store listing (set when published).
const WEB_STORE_URL = process.env.NEXT_PUBLIC_CHROME_WEB_STORE_URL || "";


const COPY = {
  bn: {
    back: "← হোমে ফিরুন",
    eyebrow: "ব্রাউজার এক্সটেনশন",
    title: "TrustLens Chrome এক্সটেনশন ইনস্টল করুন",
    intro:
      "যেকোনো ওয়েবপেজ বা সোশ্যাল পোস্টে সরাসরি দাবি যাচাই করুন — পেজ ছাড়াই, এক ক্লিকে।",
    storeBtn: "Chrome Web Store-এ পান",
    zipBtn: "এক্সটেনশন ডাউনলোড করুন (.zip)",
    manualTitle: "ম্যানুয়াল ইনস্টলেশন (Developer Mode)",
    note: "এক্সটেনশনটি এখনো Chrome Web Store-এ প্রকাশিত হয়নি — উপরের বাটন থেকে .zip ডাউনলোড করে নিচের ধাপগুলো অনুসরণ করুন।",
    steps: [
      "উপরের \"এক্সটেনশন ডাউনলোড করুন\" বাটনে ক্লিক করে .zip ফাইলটি নামান।",
      ".zip ফাইলটি একটি ফোল্ডারে আনজিপ (extract) করুন।",
      "Chrome-এ chrome://extensions খুলুন।",
      "উপরের ডানদিকে \"Developer mode\" চালু করুন।",
      "\"Load unpacked\" ক্লিক করে আনজিপ করা ফোল্ডারটি নির্বাচন করুন।",
      "TrustLens আইকন টুলবারে আসবে — যেকোনো পেজে ক্লিক করে যাচাই শুরু করুন।",
    ],

    featuresTitle: "এক্সটেনশন কী করে",
    features: [
      "নির্বাচিত টেক্সট বা পুরো পেজের দাবি যাচাই করে।",
      "৬টি বিশ্বাসযোগ্যতা স্তম্ভে স্কোর দেখায়।",
      "বাংলা ও ইংরেজি — দুই ভাষাতেই কাজ করে।",
      "সাম্প্রতিক যাচাইয়ের ইতিহাস সংরক্ষণ করে।",
    ],
  },
  en: {
    back: "← Back to home",
    eyebrow: "Browser extension",
    title: "Install the TrustLens Chrome extension",
    intro:
      "Verify claims right on any webpage or social post — one click, no copy-pasting.",
    storeBtn: "Get it on the Chrome Web Store",
    zipBtn: "Download the extension (.zip)",
    manualTitle: "Manual install (Developer Mode)",
    note: "The extension isn't on the Chrome Web Store yet — download the .zip above and load it manually with the steps below.",
    steps: [
      'Click "Download the extension (.zip)" above to get the file.',
      "Unzip (extract) the .zip into a folder.",
      "Open chrome://extensions in Chrome.",
      'Turn on "Developer mode" (top-right toggle).',
      'Click "Load unpacked" and select the unzipped folder.',
      "The TrustLens icon appears in your toolbar — click it on any page to verify.",
    ],

    featuresTitle: "What the extension does",
    features: [
      "Checks claims from selected text or the whole page.",
      "Shows scores across all 6 trust pillars.",
      "Works in both Bangla and English.",
      "Keeps a local history of your recent checks.",
    ],
  },
} as const;

export default function GetExtensionPage() {
  const { language } = useStore();
  const c = COPY[language] ?? COPY.en;

  return (
    <div className="flex flex-col gap-8 md:gap-10 mobile-bottom-pad">
      <header className="sticky top-0 z-20 -mx-6 md:-mx-10 lg:-mx-16 px-6 md:px-10 lg:px-16 py-3.5 backdrop-blur-xl bg-surface-0/85 border-b border-surface-3/40">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2.5 shrink-0 text-text-primary">
            <Logo size={28} showWordmark />
          </Link>
          <div className="flex items-center gap-1.5">
            <ThemeToggle />
            <LanguageToggle />
          </div>
        </div>
      </header>

      <motion.section
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="flex flex-col gap-4 max-w-2xl"
      >
        <Link href="/" className="text-[12px] text-text-tertiary hover:text-text-primary transition-colors w-fit">
          {c.back}
        </Link>
        <p className="text-[10px] uppercase tracking-[0.08em] text-text-tertiary">{c.eyebrow}</p>
        <h1 className="text-[clamp(1.6rem,5vw,2.6rem)] leading-[1.1] font-semibold tracking-[-0.02em] text-text-primary font-bengali">
          {c.title}
        </h1>
        <p className="text-[15px] leading-[1.7] text-text-secondary font-bengali">{c.intro}</p>

        <div className="flex flex-wrap gap-2.5 mt-1">
          {WEB_STORE_URL && (
            <a
              href={WEB_STORE_URL}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-center justify-center gap-1.5 text-[13px] font-medium px-4 py-2.5 rounded-lg bg-surface-2 text-text-primary hover:bg-surface-3/60 transition-colors"
            >
              {c.storeBtn}
            </a>
          )}
          <a
            href={EXTENSION_ZIP_URL}
            download
            className="inline-flex items-center justify-center gap-1.5 text-[13px] font-medium px-4 py-2.5 rounded-lg bg-accent-blue text-white hover:bg-[color-mix(in_srgb,var(--accent-blue)_92%,white)] transition-colors"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            {c.zipBtn}
          </a>
        </div>

      </motion.section>

      {/* Manual install */}
      <section className="flex flex-col gap-4 max-w-2xl">
        <h2 className="text-[18px] font-semibold heading-tight text-text-primary">{c.manualTitle}</h2>
        <p className="text-[13px] text-text-tertiary leading-[1.6] font-bengali">{c.note}</p>
        <ol className="section-surface overflow-hidden divide-y divide-surface-3/40">
          {c.steps.map((step, i) => (
            <li key={i} className="flex items-start gap-3 px-4 py-3.5 md:px-5 md:py-4">
              <span className="shrink-0 font-mono text-[11px] tracking-[0.04em] text-accent-blue bg-accent-blue/10 px-2 py-0.5 rounded-md mt-0.5">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="text-[13px] md:text-[14px] text-text-secondary leading-[1.6] font-bengali">
                {step}
              </span>
            </li>
          ))}
        </ol>
      </section>

      {/* Features */}
      <section className="flex flex-col gap-4 max-w-2xl">
        <h2 className="text-[18px] font-semibold heading-tight text-text-primary">{c.featuresTitle}</h2>
        <ul className="grid gap-2 sm:grid-cols-2">
          {c.features.map((f, i) => (
            <li key={i} className="card flex items-start gap-2.5 px-4 py-3">
              <span className="mt-1 h-1.5 w-1.5 rounded-full bg-accent-blue shrink-0" />
              <span className="text-[13px] text-text-secondary leading-[1.55] font-bengali">{f}</span>
            </li>
          ))}
        </ul>
      </section>

      <footer className="pt-6 mt-2 border-t border-surface-3/40 flex items-center gap-2 text-[12px] text-text-tertiary">
        <Logo size={18} />
        <span>© 2026 TrustLens</span>
      </footer>
    </div>
  );
}
