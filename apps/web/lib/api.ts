export interface ImageAsset {
  id: string;
  source: "fixture" | "gmail" | "pinterest" | "generated";
  image_url: string;
  alt_text: string;
  mime_type: string;
}

export interface GapDimension {
  key: string;
  label: string;
  aspiration: number;
  behavior: number;
  gap: number;
}

export interface EvidenceItem {
  id: string;
  source: string;
  label: string;
  kind: "aspirational" | "purchase" | "survey";
}

export interface GroundedInsight {
  title: string;
  body: string;
  evidence_ids: string[];
}

export interface ScoreProvenance {
  aspirational_item_count: number;
  purchase_item_count: number;
  kept_purchase_count: number;
  returned_item_count: number;
  profile_method: "fixture_item_average" | "agent_profiles";
}

export interface VisionTheme {
  name: string;
  strength: number;
  confidence: number;
  evidence_ids: string[];
}

export interface GeneratedPortrait {
  kind: "style_world" | "purchase_reality";
  title: string;
  image: ImageAsset;
  evidence_ids: string[];
  model: string;
  generation_mode: "fixture" | "openai";
}

export interface GapReport {
  persona_id: string;
  persona_name: string;
  summary: string;
  gap_score: number;
  dimensions: GapDimension[];
  insights: GroundedInsight[];
  evidence: EvidenceItem[];
  score_provenance: ScoreProvenance;
  vision_themes: VisionTheme[];
  portraits: GeneratedPortrait[];
}

export type SurveyPromptKey =
  | "emotional_feedback"
  | "usage_frequency"
  | "purchase_motivation"
  | "return_reason"
  | "return_sentiment";

export interface SurveyPrompt {
  id: string;
  key: SurveyPromptKey;
  question: string;
  options: string[];
}

export interface PurchaseSurveyItem {
  id: string;
  item_id: string;
  item_name: string;
  merchant: string;
  price: number | null;
  currency: string;
  purchased_at: string;
  returned: boolean;
  image: ImageAsset | null;
  prompts: SurveyPrompt[];
  comment_prompt: string;
}

export interface DemoResponse {
  persona: Record<string, string>;
  report: GapReport;
  survey: PurchaseSurveyItem[];
}

export interface SurveyAnswer {
  item_id: string;
  values: Record<string, string>;
  notes: string;
}

export interface SourceConnection {
  source: "gmail" | "pinterest";
  configured: boolean;
  connected: boolean;
  environment: "gmail" | "sandbox";
  connect_url: string;
}

export interface ConnectionOverview {
  data_mode: string;
  sources: SourceConnection[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `RealCart API returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export function loadDemo(): Promise<DemoResponse> {
  return fetchJson<DemoResponse>("/api/demo");
}

export function loadConnections(): Promise<ConnectionOverview> {
  return fetchJson<ConnectionOverview>("/api/connections");
}

export function submitAnalysis(answers: SurveyAnswer[]): Promise<DemoResponse> {
  return fetchJson<DemoResponse>("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
}
