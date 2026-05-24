/**
 * Internationalization strings for Bengali/English.
 */

export const strings = {
  bn: {
    trustScore: "বিশ্বাসযোগ্যতা স্কোর",
    analyze: "বিশ্লেষণ করুন",
    analyzing: "বিশ্লেষণ চলছে...",
    sourceVerification: "উৎস যাচাই",
    contentConsistency: "বিষয়বস্তু সামঞ্জস্য",
    languageAnalysis: "ভাষা বিশ্লেষণ",
    bengaliContext: "বাংলা প্রসঙ্গ",
    imageVerification: "ছবি যাচাই",
    authorAnalysis: "লেখক বিশ্লেষণ",
    results: "ফলাফল",
    evidence: "প্রমাণ",
    trustworthy: "বিশ্বাসযোগ্য",
    questionable: "সন্দেহজনক",
    unreliable: "অবিশ্বাসযোগ্য",
    placeholder: "পোস্ট বা লিংক পেস্ট করুন...",
    newAnalysis: "নতুন বিশ্লেষণ",
    checkingSources: "উৎস যাচাই করা হচ্ছে...",
    analyzingLanguage: "ভাষা বিশ্লেষণ করা হচ্ছে...",
    crossReferencing: "ক্রস-রেফারেন্সিং...",
    generatingScore: "স্কোর তৈরি করা হচ্ছে...",
  },
  en: {
    trustScore: "Trust Score",
    analyze: "Analyze",
    analyzing: "Analyzing...",
    sourceVerification: "Source Verification",
    contentConsistency: "Content Consistency",
    languageAnalysis: "Language Analysis",
    bengaliContext: "Bengali Context",
    imageVerification: "Image Verification",
    authorAnalysis: "Author Analysis",
    results: "Results",
    evidence: "Evidence",
    trustworthy: "Trustworthy",
    questionable: "Questionable",
    unreliable: "Unreliable",
    placeholder: "Paste a post or link...",
    newAnalysis: "New Analysis",
    checkingSources: "Checking sources...",
    analyzingLanguage: "Analyzing language...",
    crossReferencing: "Cross-referencing...",
    generatingScore: "Generating score...",
  },
} as const;

export type Language = keyof typeof strings;
export type StringKey = keyof (typeof strings)["en"];
