"use client";

import { Suspense } from "react";
import { ResultsContent } from "./ResultsContent";

export default function ResultsPage() {
  return (
    <Suspense fallback={<ResultsLoading />}>
      <ResultsContent />
    </Suspense>
  );
}

function ResultsLoading() {
  return (
    <div className="flex flex-col gap-12">
      <header className="flex items-center justify-between pt-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-md bg-accent-blue flex items-center justify-center">
            <span className="text-white text-body font-semibold">T</span>
          </div>
          <h1 className="text-section-header font-semibold heading-tight text-text-primary">
            TrustLens
          </h1>
        </div>
      </header>
      <div className="flex items-center justify-center py-16">
        <span className="text-body text-text-secondary">Loading...</span>
      </div>
    </div>
  );
}
