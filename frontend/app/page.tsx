"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { InputForm } from "@/components/InputForm";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Logo } from "@/components/Logo";
import { MobileBottomNav } from "@/components/MobileBottomNav";
import { useStore } from "@/lib/store";
import { useI18n } from "@/lib/useI18n";
import { loadRecentScans, type RecentScanItem } from "@/lib/recentScans";

const BOT_SOURCE_URL =
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  "https://github.com/mahdiebene/TrustLensAI/tree/main/bot";
const EXTENSION_SOURCE_URL =
  process.env.NEXT_PUBLIC_CHROME_EXTENSION_URL ||
  "https://github.com/mahdiebene/TrustLensAI/tree/main/extension";

const HOW_STEPS = [
  { num: "01", titleKey: "pasteContent", descKey: "pasteContentDesc" },
  { num: "02", titleKey: "aiAnalyzes", descKey: "aiAnalyzesDesc" },
  { num: "03", titleKey: "getScore", descKey: "getScoreDesc" },
  { num: "04", titleKey: "trustVerdict", descKey: "trustVerdictDesc" },
] as const;

const PILLAR_ROWS = [
  { titleKey: "sourceVerification", descKey: "sourceVerificationDesc" },
  { titleKey: "contentConsistency", descKey: "contentConsistencyDesc" },
  { titleKey: "languageAnalysis", descKey: "languageAnalysisDesc" },
  { titleKey: "bengaliContext", descKey: "bengaliContextDesc" },
  { titleKey: "imageVerification", descKey: "imageAuthenticityDesc" },
  { titleKey: "authorAnalysis", descKey: "authorNetworkDesc" },
] as const;

export default function HomePage() {
  const t = useI18n();
  const { language } = useStore();
  const [recentScans, setRecentScans] = useState<RecentScanItem[]>([]);

  useEffect(() => {
    const refresh = () => setRecentScans(loadRecentScans());
    refresh();
    window.addEventListener("storage", refresh);
    return () => window.removeEventListener("storage", refresh);
  }, []);

  return (
    <div className="flex flex-col gap-10 md:gap-14 mobile-bottom-pad">
      {/* ─────────── Header ─────────── */}
      <header className="sticky top-0 z-20 -mx-6 md:-mx-10 lg:-mx-16 px-6 md:px-10 lg:px-16 py-3.5 backdrop-blur-xl bg-surface-0/85 border-b border-surface-3/40">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2.5 shrink-0 text-text-primary">
            <Logo size={28} showWordmark />
          </Link>

          <nav className="hidden md:flex items-center gap-7 text-[13px] text-text-secondary">
            <a href="#verify" className="hover:text-text-primary transition-colors duration-150">{t.verifyContent}</a>
            <a href="#how" className="hover:text-text-primary transition-colors duration-150">{t.howItWorks}</a>
            <a href="#tools" className="hover:text-text-primary transition-colors duration-150">{t.botExtension}</a>
            <a href="#scans" className="hover:text-text-primary transition-colors duration-150">{t.recentScanned}</a>
          </nav>

          <div className="flex items-center gap-1.5">
            <ThemeToggle />
            <LanguageToggle />
          </div>
        </div>
      </header>

      {/* ─────────── Hero + Verify ───────────
          Mobile order: tight headline → INPUT FIRST (above fold) → blurb → feature stats.
          Desktop: classic 2-column with hero on the left, input on the right.
       */}
      <section id="verify" className="flex flex-col gap-5 md:grid md:grid-cols-[1.05fr_0.95fr] md:gap-10 md:items-start md:pt-2">
        {/* ── Hero text (mobile: order-1, compact) ── */}
        <div className="flex flex-col gap-3.5 md:gap-6 order-1 md:order-none">
          <div className="flex flex-wrap items-center gap-1.5 md:gap-2">
            <Pill tone="accent">{t.sixSignalBadge}</Pill>
            <Pill tone="surface">{t.bilingualBadge}</Pill>
            <Pill tone="surface" className="hidden sm:inline-flex">{t.realtimeBadge}</Pill>
          </div>

          <h2
            lang={language}
            className="text-[clamp(1.7rem,6.4vw,3.6rem)] leading-[1.08] md:leading-[1.05] font-semibold tracking-[-0.02em] text-text-primary font-bengali"
          >
            {t.tagline}
          </h2>

          {/* Blurb hidden on mobile to keep input above the fold; visible md+ */}
          <p className="hidden md:block text-[15px] md:text-[16px] leading-[1.7] text-text-secondary max-w-prose font-bengali">
            {t.heroBlurb}
          </p>

          {/* Feature stats: desktop only — they duplicate the badges on mobile */}
          <div className="hidden md:grid grid-cols-3 gap-3 max-w-2xl">
            <FeatureStat title={t.statsPillarsTitle} desc={t.statsPillarsDesc} />
            <FeatureStat title={t.statsBilingualTitle} desc={t.statsBilingualDesc} />
            <FeatureStat title={t.statsExplainableTitle} desc={t.statsExplainableDesc} />
          </div>
        </div>

        {/* ── Input card (mobile: order-2, immediately visible after headline) ── */}
        <div className="section-surface p-4 md:p-5 lg:p-6 flex flex-col gap-3.5 md:gap-4 self-start w-full order-2 md:order-none">
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] uppercase tracking-[0.08em] text-text-tertiary">
                {t.reportSection}
              </span>
              <h3 className="text-[17px] md:text-[18px] font-semibold heading-tight text-text-primary">
                {t.verifyTrustworthiness}
              </h3>
            </div>
            <span className="text-[10px] uppercase tracking-[0.08em] px-2 py-0.5 rounded-md bg-accent-blue/10 text-accent-blue shrink-0">
              {t.beta}
            </span>
          </div>
          <InputForm />
          <p className="text-[11.5px] md:text-[12px] text-text-tertiary leading-[1.55] pt-2.5 border-t border-surface-3/40">
            {t.pastePrompt}
          </p>
        </div>

        {/* ── Blurb (mobile-only, AFTER the input — secondary context) ── */}
        <p className="md:hidden order-3 text-[14px] leading-[1.7] text-text-secondary font-bengali -mt-1">
          {t.heroBlurb}
        </p>
      </section>

      {/* ─────────── How it works ─────────── */}
      <section id="how" className="flex flex-col gap-5">
        <SectionHeader eyebrow={t.howItWorks} title={t.howItWorks} />
        <ol className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {HOW_STEPS.map((step, i) => (
            <HowStep
              key={step.num}
              index={i}
              num={step.num}
              title={t[step.titleKey] as string}
              desc={t[step.descKey] as string}
            />
          ))}
        </ol>
      </section>

      {/* ─────────── 6 Pillars (table-style per sketch) ─────────── */}
      <section className="flex flex-col gap-5">
        <SectionHeader eyebrow={t.trustPillarsTitle} title={t.trustPillarsTitle} desc={t.trustPillarsDesc} />
        <div className="section-surface overflow-hidden">
          <ul className="divide-y divide-surface-3/40">
            {PILLAR_ROWS.map((row) => (
              <PillarRow
                key={row.titleKey}
                title={t[row.titleKey] as string}
                desc={t[row.descKey] as string}
              />
            ))}
          </ul>
        </div>
      </section>

      {/* ─────────── Tools / Bot & Extension ─────────── */}
      <section id="tools" className="flex flex-col gap-5">
        <SectionHeader eyebrow={t.botExtension} title={t.downloadTitle} desc={t.downloadDesc} />
        <div className="grid gap-3 md:grid-cols-3">
          <ToolCard
            title={t.toolTelegramTitle}
            copy={t.toolTelegramCopy}
            cta={t.viewSource}
            href={BOT_SOURCE_URL}
            external
            status={t.comingSoon}
            tone="muted"
            icon={<IconBot />}
          />
          <ToolCard
            title={t.toolExtensionTitle}
            copy={t.toolExtensionCopy}
            cta={t.viewSource}
            href={EXTENSION_SOURCE_URL}
            external
            status={t.comingSoon}
            tone="muted"
            icon={<IconExt />}
          />
          <ToolCard
            title={t.toolDashboardTitle}
            copy={t.toolDashboardCopy}
            cta={t.startAnalysis.replace(/[→\s]+$/, "")}
            href="#verify"
            status={t.available}
            tone="active"
            icon={<IconDash />}
          />
        </div>
        <p className="text-[12px] text-text-tertiary mt-1">{t.notProduction}</p>
      </section>

      {/* ─────────── Recently Scanned ─────────── */}
      <section id="scans" className="flex flex-col gap-5">
        <SectionHeader eyebrow={t.recentScanned} title={t.recentScanned} />
        {recentScans.length > 0 ? (
          <ul className="grid gap-2">
            {recentScans.map((item) => (
              <RecentScanRow key={item.id} item={item} language={language} t={t} />
            ))}
          </ul>
        ) : (
          <div className="section-surface flex flex-col items-center text-center gap-2 py-10 px-6">
            <span className="h-9 w-9 rounded-full bg-surface-2 border border-surface-3/60 flex items-center justify-center text-text-tertiary">
              <IconHistorySm />
            </span>
            <p className="text-[14px] text-text-secondary">{t.recentScansEmpty}</p>
            <p className="text-[12px] text-text-tertiary max-w-sm">{t.recentScansEmptyHint}</p>
          </div>
        )}
      </section>

      {/* ─────────── Footer ─────────── */}
      <footer className="pt-6 mt-2 border-t border-surface-3/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[12px] text-text-tertiary">
        <div className="flex items-center gap-2">
          <Logo size={18} />
          <span>{t.footerDesc}</span>
        </div>
        <div className="flex items-center gap-3">
          <span>{t.builtBy}</span>
          <span>•</span>
          <span>© 2026</span>
        </div>
      </footer>

      <MobileBottomNav />
    </div>
  );
}

/* ─────────── Sub-components ─────────── */

function Pill({
  children,
  tone = "surface",
  className = "",
}: {
  children: React.ReactNode;
  tone?: "surface" | "accent";
  className?: string;
}) {
  if (tone === "accent") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent-blue/10 text-accent-blue text-[11px] font-medium tracking-[-0.005em] ${className}`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-accent-blue" />
        {children}
      </span>
    );
  }
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full bg-surface-2 border border-surface-3/50 text-[11px] font-medium text-text-secondary tracking-[-0.005em] ${className}`}
    >
      {children}
    </span>
  );
}

function FeatureStat({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="card p-4 flex flex-col gap-1">
      <span className="text-[14px] font-semibold heading-tight text-text-primary">{title}</span>
      <span className="text-[12px] text-text-secondary leading-[1.6] font-bengali">{desc}</span>
    </div>
  );
}

function SectionHeader({ eyebrow, title, desc }: { eyebrow: string; title: string; desc?: string }) {
  return (
    <div className="flex flex-col gap-1.5 max-w-2xl">
      <p className="text-[10px] uppercase tracking-[0.08em] text-text-tertiary">{eyebrow}</p>
      <h3 className="text-[22px] md:text-[26px] font-semibold heading-tight text-text-primary">{title}</h3>
      {desc && <p className="text-[14px] text-text-secondary leading-[1.6] mt-1 font-bengali">{desc}</p>}
    </div>
  );
}

function HowStep({ index, num, title, desc }: { index: number; num: string; title: string; desc: string }) {
  return (
    <motion.li
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: [0.22, 1, 0.36, 1] }}
      className="card p-4 flex flex-col gap-2.5"
    >
      <div className="flex items-center gap-2.5">
        <span className="font-mono text-[11px] tracking-[0.04em] text-accent-blue bg-accent-blue/10 px-2 py-0.5 rounded-md">
          {num}
        </span>
        <h4 className="text-[14px] font-semibold heading-tight text-text-primary">{title}</h4>
      </div>
      <p className="text-[12px] text-text-secondary leading-[1.65] font-bengali">{desc}</p>
    </motion.li>
  );
}

function PillarRow({ title, desc }: { title: string; desc: string }) {
  return (
    <li className="grid grid-cols-[140px_1fr] md:grid-cols-[200px_1fr] gap-4 px-4 py-3.5 md:px-5 md:py-4 hover:bg-surface-2/50 transition-colors duration-150">
      <span className="text-[13px] md:text-[14px] font-semibold heading-tight text-text-primary font-bengali">{title}</span>
      <span className="text-[12px] md:text-[13px] text-text-secondary leading-[1.65] font-bengali">{desc}</span>
    </li>
  );
}

function ToolCard({
  title,
  copy,
  cta,
  href,
  external,
  status,
  tone,
  icon,
}: {
  title: string;
  copy: string;
  cta: string;
  href: string;
  external?: boolean;
  status: string;
  tone: "active" | "muted";
  icon: React.ReactNode;
}) {
  const isActive = tone === "active";
  return (
    <div className="card p-4 flex flex-col gap-3 h-full">
      <div className="flex items-start justify-between gap-3">
        <span className="h-9 w-9 rounded-lg bg-surface-2 text-text-primary flex items-center justify-center">
          {icon}
        </span>
        <span
          className={`text-[10px] uppercase tracking-[0.06em] px-2 py-0.5 rounded-md ${
            isActive
              ? "bg-trust-high/12 text-trust-high"
              : "bg-surface-2 text-text-tertiary"
          }`}
        >
          {status}
        </span>
      </div>
      <h4 className="text-[14px] font-semibold heading-tight text-text-primary">{title}</h4>
      <p className="text-[12px] text-text-secondary leading-[1.65] font-bengali flex-1">{copy}</p>
      <a
        href={href}
        target={external ? "_blank" : undefined}
        rel={external ? "noreferrer noopener" : undefined}
        className={`mt-1 inline-flex items-center justify-center gap-1.5 text-[12px] font-medium px-3 py-2 rounded-lg transition-colors duration-150 ${
          isActive
            ? "bg-accent-blue text-white hover:bg-[color-mix(in_srgb,var(--accent-blue)_92%,white)]"
            : "bg-surface-2 text-text-primary hover:bg-surface-3/60"
        }`}
      >
        {cta}
        {external && <IconExternalSm />}
      </a>
    </div>
  );
}

function RecentScanRow({
  item,
  language,
  t,
}: {
  item: RecentScanItem;
  language: "bn" | "en";
  t: ReturnType<typeof useI18n>;
}) {
  const verdictTone = verdictToneFor(item.verdictEn);
  const verdictLabel = language === "bn" ? item.verdictBn : item.verdictEn;
  return (
    <li className="card flex items-center gap-2.5 px-3 py-2.5 min-w-0 overflow-hidden">
      <span className="h-7 w-7 shrink-0 rounded-md bg-surface-2 text-text-secondary flex items-center justify-center text-[10px] uppercase tracking-[0.06em] font-semibold">
        {item.source === "link" ? "URL" : "Aa"}
      </span>
      <p className="flex-1 min-w-0 text-[13px] text-text-primary font-bengali truncate">
        {item.excerpt}
      </p>
      <span
        className={`shrink-0 max-w-[40%] truncate px-2 py-1 rounded-md text-[11px] font-medium tracking-[-0.005em] ${
          verdictTone === "high"
            ? "bg-trust-high/12 text-trust-high"
            : verdictTone === "low"
            ? "bg-trust-low/12 text-trust-low"
            : "bg-trust-medium/12 text-trust-medium"
        }`}
      >
        {verdictLabel}
      </span>
    </li>
  );
}

function verdictToneFor(verdictEn: string): "high" | "medium" | "low" {
  const v = (verdictEn || "").toLowerCase();
  if (v.includes("true") && !v.includes("not")) return "high";
  if (v.includes("false") || v.includes("unreliable") || v.includes("not")) return "low";
  return "medium";
}

/* ---------- Inline icons (kept tiny, single-stroke) ---------- */

function IconBot() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="7" width="16" height="12" rx="3" />
      <path d="M12 3 V7" />
      <circle cx="9" cy="13" r="1" />
      <circle cx="15" cy="13" r="1" />
      <path d="M9 17 H15" />
    </svg>
  );
}

function IconExt() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 4 V8 H4 V14 H9 V8 H15 V4 Z" />
      <path d="M15 14 V20 H9 V14" />
      <path d="M15 14 H20 V20 H15 Z" />
    </svg>
  );
}

function IconDash() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M3.5 12 H8 L10 8 L14 16 L16 12 H20.5" />
    </svg>
  );
}

function IconHistorySm() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 12 A9 9 0 1 0 6 5.5" />
      <polyline points="3 4 3 10 9 10" />
      <path d="M12 8 V12 L15 14" />
    </svg>
  );
}

function IconExternalSm() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 4 H20 V10" />
      <path d="M20 4 L11 13" />
      <path d="M9 6 H6 A2 2 0 0 0 4 8 V18 A2 2 0 0 0 6 20 H16 A2 2 0 0 0 18 18 V15" />
    </svg>
  );
}
