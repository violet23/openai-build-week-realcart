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

export interface AnalysisStage {
  name: string;
  status: "completed";
  detail: string;
}

export interface ModelRuntime {
  provider: "fixture" | "openai";
  specialist_model: string | null;
  specialist_reasoning_effort: string | null;
  synthesis_model: string | null;
  synthesis_reasoning_effort: string | null;
  trace_id: string | null;
}

export interface AnalysisRun {
  data_mode: string;
  analysis_mode: string;
  model_runtime: ModelRuntime;
  stages: AnalysisStage[];
  report: GapReport;
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

export function loadAnalysisRun(): Promise<AnalysisRun> {
  return fetchJson<AnalysisRun>("/api/run");
}
