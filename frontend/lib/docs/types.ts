export type PublishMode = "window" | "duration";

export interface DocsVisibilityConfig {
  enabled: boolean;
  mode: PublishMode;
  startAtIso: string;
  endAtIso: string;
  durationHours: number;
  updatedAtIso: string;
  updatedBy: string;
}

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  email: string;
  photoUrl: string;
}

export interface FeatureItem {
  id: string;
  name: string;
  status: "live" | "upcoming" | "planned";
  note: string;
  source: "frontend" | "backend" | "platform";
}

export interface DeckSection {
  id: string;
  title: string;
  summary: string;
  details: string;
}

export interface DocsContent {
  updatedAtIso: string;
  version: string;
  teamName: string;
  deck: DeckSection[];
  productOverview: string;
  architectureMermaid: string;
  dataFlowMermaid: string;
  technologyStack: Record<string, string[]>;
  apiDocumentation: string;
  dataLayer: string;
  aiLayer: string;
  roadmap: Record<string, string[]>;
  performance: string;
  security: string;
  analytics: string;
  changelog: Array<{ version: string; dateIso: string; notes: string }>;
  teamMembers: TeamMember[];
  features: FeatureItem[];
}

export interface DocsVersionSnapshot {
  id: string;
  createdAtIso: string;
  createdBy: string;
  content: DocsContent;
}

export interface DocsAccessState {
  isPublic: boolean;
  reason: "disabled" | "before_window" | "after_window" | "active";
  nowIso: string;
  startsInMs: number;
  endsInMs: number;
}

export interface DocsLiveState {
  serverTimeIso: string;
  appVersion: string;
  backendHealth: "ok" | "degraded";
  backendDetails: Record<string, string>;
  lastPublishIso: string;
  totalVersions: number;
  liveFeatureCount: number;
  upcomingFeatureCount: number;
  plannedFeatureCount: number;
}
