import { create } from "zustand";

interface AnalysisResult {
  trust_score: number;
  verdict: string;
  verdict_bn: string;
  pillars: Array<{
    name: string;
    name_bn: string;
    score: number;
    weight: number;
    explanation_en: string;
    explanation_bn: string;
    evidence: string[];
    active: boolean;
  }>;
  explanation_en: string;
  explanation_bn: string;
  confidence: number;
  cached: boolean;
  processing_time_ms: number;
}

type Theme = "light" | "dark" | "system";

interface AppState {
  language: "bn" | "en";
  setLanguage: (lang: "bn" | "en") => void;
  theme: Theme;
  setTheme: (theme: Theme) => void;
  isAnalyzing: boolean;
  setIsAnalyzing: (v: boolean) => void;
  analysisStatus: string;
  setAnalysisStatus: (s: string) => void;
  result: AnalysisResult | null;
  setResult: (r: AnalysisResult | null) => void;
}

export const useStore = create<AppState>((set) => ({
  language: "bn",
  setLanguage: (lang) => set({ language: lang }),
  theme: "system",
  setTheme: (theme) => set({ theme }),
  isAnalyzing: false,
  setIsAnalyzing: (v) => set({ isAnalyzing: v }),
  analysisStatus: "",
  setAnalysisStatus: (s) => set({ analysisStatus: s }),
  result: null,
  setResult: (r) => set({ result: r }),
}));
