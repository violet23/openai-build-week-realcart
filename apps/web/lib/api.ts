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

export interface GapReport {
  persona_id: string;
  persona_name: string;
  summary: string;
  gap_score: number;
  dimensions: GapDimension[];
  insights: GroundedInsight[];
  evidence: EvidenceItem[];
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
  price: number;
  currency: string;
  purchased_at: string;
  returned: boolean;
  prompts: SurveyPrompt[];
  comment_prompt: string;
}

export interface CandidateItem {
  name: string;
  price: number;
  dimensions: Record<string, number>;
}

export interface DemoResponse {
  persona: Record<string, string>;
  report: GapReport;
  survey: PurchaseSurveyItem[];
  candidate: CandidateItem;
}

export interface OpinionDimension {
  label: string;
  score: number;
  note: string;
}

export interface SecondOpinionResponse {
  candidate_name: string;
  reading: string;
  dimensions: OpinionDimension[];
  evidence_ids: string[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`RealCart API returned ${response.status}`);
  }
  return (await response.json()) as T;
}

export function loadDemo(): Promise<DemoResponse> {
  return fetchJson<DemoResponse>("/api/demo");
}

export function loadSecondOpinion(
  candidate: CandidateItem,
): Promise<SecondOpinionResponse> {
  return fetchJson<SecondOpinionResponse>("/api/second-opinion", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(candidate),
  });
}
