import { InputForm } from "@/components/InputForm";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-12">
      {/* Header — minimal, tool-like */}
      <header className="flex items-center justify-between pt-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-md bg-accent-blue flex items-center justify-center">
            <span className="text-white text-body font-semibold">T</span>
          </div>
          <h1 className="text-section-header font-semibold heading-tight text-text-primary">
            TrustLens
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-caption text-text-tertiary caps-wide uppercase">
            Beta
          </span>
        </div>
      </header>

      {/* Input Section */}
      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-body text-text-secondary">
            পোস্ট, আর্টিকেল বা লিংক বিশ্লেষণ করুন
          </h2>
        </div>
        <InputForm />
      </section>
    </div>
  );
}
