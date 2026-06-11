"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useStore } from "@/lib/store";

// Public Telegram bot. Env can override the handle if it ever changes.
const BOT_HANDLE = process.env.NEXT_PUBLIC_TELEGRAM_BOT_HANDLE || "TrustLensAI_bot";
const BOT_URL =
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || `https://t.me/${BOT_HANDLE}`;

const COPY = {
  bn: {
    back: "← হোমে ফিরুন",
    eyebrow: "টেলিগ্রাম বট",
    title: "TrustLens টেলিগ্রাম বট ব্যবহার করুন",
    intro:
      "যেকোনো টেক্সট, লিংক, ফরোয়ার্ড করা পোস্ট বা ছবি বটকে পাঠান — টেলিগ্রামেই তাৎক্ষণিক বিশ্বাসযোগ্যতা যাচাই।",
    openBtn: "টেলিগ্রামে বট খুলুন",
    handleLabel: "বট হ্যান্ডেল",
    startTitle: "কীভাবে শুরু করবেন",
    steps: [
      "উপরের \"টেলিগ্রামে বট খুলুন\" বাটনে ক্লিক করুন (অথবা টেলিগ্রামে @" + BOT_HANDLE + " সার্চ করুন)।",
      "\"Start\" চাপুন — বট স্বাগত বার্তা পাঠাবে।",
      "যেকোনো খবরের লিংক, পোস্ট, লেখা বা ছবি বটকে পাঠান বা ফরোয়ার্ড করুন।",
      "কয়েক সেকেন্ডে ট্রাস্ট স্কোর, রায় ও ৬টি স্তম্ভের বিশ্লেষণ পেয়ে যাবেন।",
    ],
    cmdTitle: "কমান্ডসমূহ",
    commands: [
      { cmd: "/start", desc: "স্বাগত বার্তা ও ব্যবহারবিধি" },
      { cmd: "/analyze <লেখা>", desc: "নির্দিষ্ট লেখা যাচাই করুন" },
      { cmd: "/lang", desc: "ভাষা পরিবর্তন (/lang en, /lang bn)" },
      { cmd: "/help", desc: "ব্যবহারে সাহায্য" },
      { cmd: "/about", desc: "TrustLens সম্পর্কে" },
    ],
    featuresTitle: "বট কী করে",
    features: [
      "টেক্সট, লিংক, ফরোয়ার্ড করা পোস্ট বা ছবি — সবই যাচাই করে।",
      "ট্রাস্ট স্কোর, রায় ও প্রতি স্তম্ভের বিশ্লেষণ দেখায়।",
      "বাংলা ও ইংরেজি — দুই ভাষাতেই কাজ করে।",
      "সম্পূর্ণ ওয়েব রিপোর্টের লিংক দেয়।",
    ],
    note: "শুধু একটি মেসেজ বা ছবি পাঠালেই বট সেটি যাচাই করে দেয় — আলাদা কমান্ড লাগে না।",
  },
  en: {
    back: "← Back to home",
    eyebrow: "Telegram bot",
    title: "Use the TrustLens Telegram bot",
    intro:
      "Send any text, link, forwarded post, or image to the bot — instant credibility checks, right inside Telegram.",
    openBtn: "Open the bot in Telegram",
    handleLabel: "Bot handle",
    startTitle: "How to get started",
    steps: [
      'Tap "Open the bot in Telegram" above (or search @' + BOT_HANDLE + " in Telegram).",
      'Press "Start" — the bot sends a welcome message.',
      "Send or forward any news link, post, text, or image to the bot.",
      "In seconds you get a trust score, verdict, and the 6-pillar breakdown.",
    ],
    cmdTitle: "Commands",
    commands: [
      { cmd: "/start", desc: "Welcome message + how to use" },
      { cmd: "/analyze <text>", desc: "Analyze the text that follows" },
      { cmd: "/lang", desc: "Switch language (/lang en, /lang bn)" },
      { cmd: "/help", desc: "Usage help" },
      { cmd: "/about", desc: "About TrustLens" },
    ],
    featuresTitle: "What the bot does",
    features: [
      "Checks text, links, forwarded posts, and images.",
      "Shows trust score, verdict, and per-pillar breakdown.",
      "Works in both Bangla and English.",
      "Links out to the full web report.",
    ],
    note: "Just send (or forward) any message or image and it gets analyzed — no command needed.",
  },
} as const;

export default function GetBotPage() {
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

        <div className="flex flex-wrap items-center gap-2.5 mt-1">
          <a
            href={BOT_URL}
            target="_blank"
            rel="noreferrer noopener"
            className="inline-flex items-center justify-center gap-1.5 text-[13px] font-medium px-4 py-2.5 rounded-lg bg-accent-blue text-white hover:bg-[color-mix(in_srgb,var(--accent-blue)_92%,white)] transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M21.94 4.27a1.5 1.5 0 0 0-1.6-.2L3.4 11.2c-1.07.46-1.02 2 .08 2.39l4.3 1.5 1.66 5.02c.27.82 1.33 1 1.86.32l2.3-2.96 4.36 3.2c.65.48 1.58.12 1.74-.67l2.84-13.6a1.5 1.5 0 0 0-.6-1.45ZM9.7 14.2l8.2-5.1-6.7 6.06a1.5 1.5 0 0 0-.47.9l-.27 1.86-.76-3.62Z" />
            </svg>
            {c.openBtn}
          </a>
          <span className="inline-flex items-center gap-1.5 text-[12px] text-text-tertiary">
            {c.handleLabel}:
            <a
              href={BOT_URL}
              target="_blank"
              rel="noreferrer noopener"
              className="font-mono text-[12px] text-text-secondary hover:text-text-primary transition-colors"
            >
              @{BOT_HANDLE}
            </a>
          </span>
        </div>
      </motion.section>

      {/* Get started */}
      <section className="flex flex-col gap-4 max-w-2xl">
        <h2 className="text-[18px] font-semibold heading-tight text-text-primary">{c.startTitle}</h2>
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

      {/* Commands */}
      <section className="flex flex-col gap-4 max-w-2xl">
        <h2 className="text-[18px] font-semibold heading-tight text-text-primary">{c.cmdTitle}</h2>
        <ul className="section-surface overflow-hidden divide-y divide-surface-3/40">
          {c.commands.map((cmd) => (
            <li key={cmd.cmd} className="grid grid-cols-[140px_1fr] md:grid-cols-[180px_1fr] gap-4 px-4 py-3 md:px-5 md:py-3.5 items-center">
              <code className="font-mono text-[12px] text-accent-blue">{cmd.cmd}</code>
              <span className="text-[13px] text-text-secondary leading-[1.55] font-bengali">{cmd.desc}</span>
            </li>
          ))}
        </ul>
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
