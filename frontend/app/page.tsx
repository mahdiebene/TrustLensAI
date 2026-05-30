"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { InputForm } from "@/components/InputForm";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useStore } from "@/lib/store";
import { useI18n } from "@/lib/useI18n";
import { loadRecentScans, type RecentScanItem } from "@/lib/recentScans";

const howItWorks = [
  { titleKey: "pasteContent", descKey: "pasteContentDesc", badge: "01" },
  { titleKey: "aiAnalyzes", descKey: "aiAnalyzesDesc", badge: "02" },
  { titleKey: "getScore", descKey: "getScoreDesc", badge: "03" },
  { titleKey: "trustVerdict", descKey: "trustVerdictDesc", badge: "04" },
];

const pillars = [
  { titleKey: "sourceVerification", descKey: "sourceVerificationDesc" },
  { titleKey: "contentConsistency", descKey: "contentConsistencyDesc" },
  { titleKey: "languageAnalysis", descKey: "languageAnalysisDesc" },
  { titleKey: "bengaliContext", descKey: "bengaliContextDesc" },
  { titleKey: "imageVerification", descKey: "imageAuthenticityDesc" },
  { titleKey: "authorAnalysis", descKey: "authorNetworkDesc" },
];

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
    <div className="flex flex-col min-h-[calc(100vh-4rem)] gap-8 md:gap-10">
      <header className="sticky top-0 z-20 -mx-6 md:-mx-10 lg:-mx-16 px-6 md:px-10 lg:px-16 py-4 backdrop-blur-md bg-surface-0/80 border-b border-surface-3/50">
        <div className="flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-3 shrink-0">
            <div className="h-10 w-10 rounded-2xl bg-accent-blue flex items-center justify-center shadow-lg shadow-accent-blue/20">
              <span className="text-white text-body font-semibold">T</span>
            </div>
            <div className="flex flex-col">
              <h1 className="text-section-header font-semibold heading-tight text-text-primary leading-none">
                TrustLens
              </h1>
              <span className="text-caption text-text-tertiary caps-wide uppercase">{t.liveTrustCheck}</span>
            </div>
          </Link>
          <nav className="hidden md:flex items-center gap-6 text-caption text-text-secondary">
            <a href="#verify" className="hover:text-text-primary transition-colors">{t.verifyContent}</a>
            <a href="#how" className="hover:text-text-primary transition-colors">{t.howItWorks}</a>
            <a href="#download" className="hover:text-text-primary transition-colors">{t.botExtension}</a>
            <a href="#scans" className="hover:text-text-primary transition-colors">{t.recentScanned}</a>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <LanguageToggle />
          </div>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr] items-start pt-2">
        <div className="flex flex-col gap-6">
          <div className="flex flex-wrap items-center gap-3 text-caption text-text-secondary">
            <span className="px-3 py-1 rounded-full bg-surface-2 border border-surface-3/50">{t.heroEyebrow}</span>
            <span className="px-3 py-1 rounded-full bg-accent-blue/10 text-accent-blue border border-accent-blue/15">{t.beta}</span>
          </div>

          <div className="flex flex-col gap-3 max-w-3xl">
            <p className="text-caption uppercase caps-wide text-text-tertiary">{t.liveTrustCheck}</p>
            <h2 className="text-[clamp(2.6rem,6vw,5.6rem)] leading-[0.92] font-semibold heading-tight text-text-primary">
              {t.tagline}
            </h2>
            <p className="text-body-bn text-text-secondary max-w-2xl font-bengali">
              {t.heroBlurb}
            </p>
            <p className="text-body text-text-secondary max-w-2xl">
              {language === "bn" ? t.subtitle : t.pasteHint}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <a href="#verify" className="px-5 py-3 rounded-2xl bg-accent-blue text-white font-medium shadow-lg shadow-accent-blue/20 hover:translate-y-[-1px] transition-transform">{t.primaryCta}</a>
            <a href="#how" className="px-5 py-3 rounded-2xl bg-surface-1 border border-surface-3/60 text-text-primary font-medium hover:bg-surface-2 transition-colors">{t.secondaryCta}</a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <MetricCard value="50M+" label={t.statsScanned} />
            <MetricCard value="0" label={t.statsKeywords} />
            <MetricCard value="96.4%" label={t.statsAccuracy} />
          </div>
        </div>

        <div id="verify" className="section-surface p-5 md:p-6 lg:p-7">
          <div className="flex items-start justify-between gap-3 mb-5">
            <div>
              <p className="text-caption uppercase caps-wide text-text-tertiary">{t.reportSection}</p>
              <h3 className="text-page-section font-semibold heading-tight text-text-primary">{t.verifyTrustworthiness}</h3>
            </div>
            <span className="px-3 py-1 rounded-full bg-surface-2 text-caption text-text-secondary">AI</span>
          </div>
          <InputForm />
          <div className="mt-4 rounded-2xl border border-dashed border-surface-3/80 bg-surface-2/60 p-4 text-caption text-text-secondary">
            {t.pastePrompt}
          </div>
        </div>
      </section>

      <section id="how" className="section-surface p-5 md:p-6 lg:p-8">
        <div className="flex flex-col gap-2 mb-6">
          <p className="text-caption uppercase caps-wide text-text-tertiary">{t.howItWorks}</p>
          <h3 className="text-page-section font-semibold heading-tight text-text-primary">{t.howItWorks}</h3>
        </div>
        <div className="grid gap-4 lg:grid-cols-4">
          {howItWorks.map((step, index) => (
            <HowStep
              key={step.titleKey}
              index={index}
              badge={step.badge}
              title={t[step.titleKey as keyof typeof t] as string}
              description={t[step.descKey as keyof typeof t] as string}
            />
          ))}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr] items-start">
        <div className="section-surface p-5 md:p-6 lg:p-8">
          <p className="text-caption uppercase caps-wide text-text-tertiary">{t.trustPillarsTitle}</p>
          <h3 className="mt-2 text-page-section font-semibold heading-tight text-text-primary">{t.trustPillarsTitle}</h3>
          <p className="mt-3 text-body text-text-secondary">{t.trustPillarsDesc}</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {pillars.map((pillar) => (
            <PillarMiniCard key={pillar.titleKey} title={t[pillar.titleKey as keyof typeof t] as string} desc={t[pillar.descKey as keyof typeof t] as string} />
          ))}
        </div>
      </section>

      <section id="download" className="section-surface p-5 md:p-6 lg:p-8">
        <div className="flex flex-col gap-2 mb-6 max-w-2xl">
          <p className="text-caption uppercase caps-wide text-text-tertiary">{t.botExtension}</p>
          <h3 className="text-page-section font-semibold heading-tight text-text-primary">{t.downloadTitle}</h3>
          <p className="text-body text-text-secondary">{t.downloadDesc}</p>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <DownloadCard icon="bot" title="Telegram Bot" copy={t.botCopy} action={t.openBot} href={BOT_SOURCE_URL} external />
          <DownloadCard icon="extension" title="Chrome Extension" copy={t.extensionCopy} action={t.openExtension} href={EXTENSION_SOURCE_URL} external />
          <DownloadCard icon="dashboard" title="Web App Dashboard" copy={t.dashboardCopy} action={t.openDashboard} href="/results" />
        </div>
      </section>

      <section id="scans" className="section-surface p-5 md:p-6 lg:p-8">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div>
            <p className="text-caption uppercase caps-wide text-text-tertiary">{t.recentScanned}</p>
            <h3 className="text-page-section font-semibold heading-tight text-text-primary">{t.recentScanned}</h3>
          </div>
          <span className="text-caption text-text-tertiary">{t.liveTrustCheck}</span>
        </div>
        <div className="grid gap-3">
          {recentScans.length > 0 ? recentScans.map((item) => (
            <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-surface-3/60 bg-surface-1 px-4 py-3">
              <div className="flex items-center gap-3 min-w-0">
                <span className="px-2.5 py-1 rounded-full bg-surface-2 text-caption text-text-secondary shrink-0">
                  {item.source === "link" ? t.recentSourceLink : t.recentSourceText}
                </span>
                <div className="min-w-0">
                  <p className="text-body text-text-primary truncate">{item.excerpt}</p>
                  <p className="text-caption text-text-tertiary">{t.reportSection}</p>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-full text-caption font-medium w-fit ${item.verdictEn === "True" ? "bg-trust-high/10 text-trust-high" : "bg-trust-low/10 text-trust-low"}`}>
                {language === "bn" ? item.verdictBn : item.verdictEn}
              </div>
            </div>
          )) : (
            <div className="rounded-2xl border border-dashed border-surface-3/70 bg-surface-1 px-4 py-6 text-center text-text-secondary">
              <p className="text-body">{t.recentScansEmpty}</p>
              <p className="text-caption mt-1">{t.recentScansEmptyHint}</p>
            </div>
          )}
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-center gap-3 rounded-3xl border border-surface-3/60 bg-surface-1 px-5 py-4 text-caption text-text-secondary">
        <Chip label={t.aiVerification} />
        <Chip label={t.factChecking} />
        <Chip label={t.transparency} />
      </section>

      <footer className="pt-4 pb-2 border-t border-surface-3/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-caption text-text-tertiary">
        <p>{t.footerDesc}</p>
        <p>{t.footerBuilt} • 2026</p>
      </footer>
    </div>
  );
}

function MetricCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-2xl border border-surface-3/60 bg-surface-1 px-4 py-4">
      <div className="text-page-section font-semibold heading-tight text-text-primary">{value}</div>
      <div className="text-caption text-text-tertiary mt-1">{label}</div>
    </div>
  );
}

function HowStep({ index, badge, title, description }: { index: number; badge: string; title: string; description: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.4 }}
      transition={{ duration: 0.35, delay: index * 0.06 }}
      className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4"
    >
      <div className="flex items-center gap-3 mb-3">
        <div className="h-10 w-10 rounded-full bg-accent-blue/10 text-accent-blue flex items-center justify-center text-caption font-semibold">{badge}</div>
        <h4 className="text-body font-medium text-text-primary">{title}</h4>
      </div>
      <p className="text-caption text-text-secondary leading-relaxed">{description}</p>
    </motion.div>
  );
}

function Chip({ label }: { label: string }) {
  return <span className="px-3 py-1 rounded-full bg-surface-2 border border-surface-3/50">{label}</span>;
}

function PillarMiniCard({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-2xl border border-surface-3/60 bg-surface-1 p-4">
      <h4 className="text-body font-medium text-text-primary">{title}</h4>
      <p className="mt-2 text-caption text-text-secondary leading-relaxed">{desc}</p>
    </div>
  );
}

function DownloadCard({ icon, title, copy, action, href, external = false }: { icon: string; title: string; copy: string; action: string; href: string; external?: boolean }) {
  const glyphs = {
    bot: "✦",
    extension: "⌘",
    dashboard: "▣",
  } as const;

  return (
    <div className="rounded-2xl border border-surface-3/60 bg-surface-1 p-5 flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <div className="h-11 w-11 rounded-2xl bg-surface-2 text-text-primary flex items-center justify-center text-body font-semibold">{glyphs[icon as keyof typeof glyphs]}</div>
        <h4 className="text-body font-medium text-text-primary">{title}</h4>
      </div>
      <p className="text-caption text-text-secondary leading-relaxed">{copy}</p>
      <a
        className="mt-auto self-start px-4 py-2 rounded-xl bg-accent-blue text-white text-caption font-medium hover:bg-accent-blue/90 transition-colors"
        href={href}
        target={external ? "_blank" : undefined}
        rel={external ? "noreferrer noopener" : undefined}
      >
        {action}
      </a>
    </div>
  );
}

const BOT_SOURCE_URL = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://github.com/mahdiebene/TrustLensAI/tree/main/bot";
const EXTENSION_SOURCE_URL = process.env.NEXT_PUBLIC_CHROME_EXTENSION_URL || "https://github.com/mahdiebene/TrustLensAI/tree/main/extension";
