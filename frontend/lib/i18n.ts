/**
 * Internationalization strings for Bengali/English.
 */

export const strings = {
  bn: {
    // Core
    trustScore: "বিশ্বাসযোগ্যতা স্কোর",
    analyze: "বিশ্লেষণ করুন",
    analyzing: "বিশ্লেষণ চলছে...",
    newAnalysis: "নতুন বিশ্লেষণ",

    // Tagline & branding
    tagline: "গুজব চিনুন, সত্য জানুন।",
    subtitle: "পোস্ট, আর্টিকেল বা লিংক বিশ্লেষণ করুন",
    footerDesc: "বাংলাদেশি সোশ্যাল মিডিয়ার জন্য AI-চালিত বিশ্বাসযোগ্যতা যাচাই প্ল্যাটফর্ম",
    footerBuilt: "তৈরি করেছে TrustLens টিম",

    // Pillars
    sourceVerification: "উৎস যাচাই",
    contentConsistency: "বিষয়বস্তু সামঞ্জস্য",
    languageAnalysis: "ভাষা বিশ্লেষণ",
    bengaliContext: "বাংলা প্রসঙ্গ",
    imageVerification: "ছবি যাচাই",
    authorAnalysis: "লেখক বিশ্লেষণ",

    // Results
    results: "ফলাফল",
    evidence: "প্রমাণ",
    explanation: "বিশ্লেষণ",
    trustworthy: "বিশ্বাসযোগ্য",
    questionable: "সন্দেহজনক",
    unreliable: "অবিশ্বাসযোগ্য",
    highlyTrustworthy: "অত্যন্ত বিশ্বাসযোগ্য",
    generallyReliable: "সাধারণত নির্ভরযোগ্য",
    likelyUnreliable: "সম্ভবত অবিশ্বাসযোগ্য",
    highRisk: "উচ্চ ঝুঁকি",

    // Input
    placeholder: "পোস্ট বা লিংক পেস্ট করুন...",
    urlDetected: "URL শনাক্ত হয়েছে",

    // Loading states
    checkingSources: "উৎস যাচাই করা হচ্ছে...",
    analyzingLanguage: "ভাষা বিশ্লেষণ করা হচ্ছে...",
    crossReferencing: "ক্রস-রেফারেন্সিং...",
    generatingScore: "স্কোর তৈরি করা হচ্ছে...",

    // Misc
    confidence: "নির্ভরযোগ্যতা",
    cached: "ক্যাশ থেকে",
    noResults: "এখনো কোনো বিশ্লেষণ ফলাফল নেই।",
    startAnalysis: "নতুন বিশ্লেষণ শুরু করুন →",
    beta: "বেটা",
  },
  en: {
    // Core
    trustScore: "Trust Score",
    analyze: "Analyze",
    analyzing: "Analyzing...",
    newAnalysis: "New Analysis",

    // Tagline & branding
    tagline: "Spot rumors, know the truth.",
    subtitle: "Analyze posts, articles, or links",
    footerDesc: "AI-Powered Trust Scoring Platform for Bangladeshi Social Media",
    footerBuilt: "Built by TrustLens Team",

    // Pillars
    sourceVerification: "Source Verification",
    contentConsistency: "Content Consistency",
    languageAnalysis: "Language Analysis",
    bengaliContext: "Bengali Context",
    imageVerification: "Image Verification",
    authorAnalysis: "Author Analysis",

    // Results
    results: "Results",
    evidence: "Evidence",
    explanation: "Analysis",
    trustworthy: "Trustworthy",
    questionable: "Questionable",
    unreliable: "Unreliable",
    highlyTrustworthy: "Highly Trustworthy",
    generallyReliable: "Generally Reliable",
    likelyUnreliable: "Likely Unreliable",
    highRisk: "High Risk",

    // Input
    placeholder: "Paste a post or link...",
    urlDetected: "URL detected",

    // Loading states
    checkingSources: "Checking sources...",
    analyzingLanguage: "Analyzing language...",
    crossReferencing: "Cross-referencing...",
    generatingScore: "Generating score...",

    // Misc
    confidence: "Confidence",
    cached: "Cached",
    noResults: "No analysis results yet.",
    startAnalysis: "Start a new analysis →",
    beta: "Beta",
  },
} as const;

export type Language = keyof typeof strings;
export type StringKey = keyof (typeof strings)["en"];

/**
 * Hook-compatible getter for i18n strings.
 * Usage: const t = getStrings('bn'); t.analyze
 */
export function getStrings(lang: Language) {
  return strings[lang];
}
