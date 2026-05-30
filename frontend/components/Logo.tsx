"use client";

/**
 * TrustLens logo — geometric shield fused with a scanning lens.
 * Pure SVG, single-stroke, follows the design skill ("flat vector, no shadows, no gradients").
 *
 * Sizing is controlled via the `size` prop (px). The mark uses currentColor so it
 * adapts to dark/light mode automatically.
 */
export function Logo({ size = 32, showWordmark = false, className = "" }: { size?: number; showWordmark?: boolean; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="shrink-0"
      >
        {/* Shield outline */}
        <path
          d="M16 2.5 L27 6.5 V15 C27 21.5 22.5 26.5 16 29.5 C9.5 26.5 5 21.5 5 15 V6.5 Z"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinejoin="round"
          fill="none"
        />
        {/* Lens — concentric circle inside the shield */}
        <circle cx="14.5" cy="14" r="4.25" stroke="currentColor" strokeWidth="1.75" fill="none" />
        {/* Lens handle / scan line — angled stroke exiting the lens */}
        <path
          d="M17.6 17.1 L21.5 21"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
        {/* Subtle accent dot — the "verified" pulse */}
        <circle cx="14.5" cy="14" r="1.1" fill="currentColor" />
      </svg>
      {showWordmark && (
        <span className="flex flex-col leading-none">
          <span className="text-[15px] font-semibold tracking-[-0.02em] text-text-primary">TrustLens</span>
          <span className="text-[10px] uppercase tracking-[0.12em] text-text-tertiary mt-0.5">Live Trust Check</span>
        </span>
      )}
    </span>
  );
}
