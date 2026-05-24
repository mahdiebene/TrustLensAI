"use client";

import { InputForm } from "@/components/InputForm";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useI18n } from "@/lib/useI18n";

export default function HomePage() {
  const t = useI18n();

  return (
    <div className="flex flex-col min-h-[calc(100vh-4rem)]">
      {/* Header — minimal, tool-like */}
      <header className="flex items-center justify-between pt-4 pb-8">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-md bg-accent-blue flex items-center justify-center">
            <span className="text-white text-body font-semibold">T</span>
          </div>
          <div className="flex flex-col">
            <h1 className="text-section-header font-semibold heading-tight text-text-primary leading-none">
              TrustLens
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LanguageToggle />
          <span className="text-caption text-text-tertiary caps-wide uppercase ml-1">
            {t.beta}
          </span>
        </div>
      </header>

      {/* Main content */}
      <section className="flex flex-col gap-6 flex-1">
        {/* Tagline */}
        <div className="flex flex-col gap-1">
          <p className="text-body-bn font-bengali text-text-primary font-medium">
            {t.tagline}
          </p>
          <p className="text-body text-text-secondary">
            {t.subtitle}
          </p>
        </div>

        {/* Input */}
        <InputForm />
      </section>

      {/* Footer — subtle */}
      <footer className="mt-16 pt-6 border-t border-surface-3/30">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <p className="text-caption text-text-tertiary">
            {t.footerDesc}
          </p>
          <p className="text-caption text-text-tertiary">
            {t.footerBuilt} • 2026
          </p>
        </div>
      </footer>
    </div>
  );
}
