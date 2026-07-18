"""Typed contracts shared by connectors, scoring, agents, and API routes."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StyleDimensions(BaseModel):
    """Fixed taxonomy shared by specialist agents and deterministic scoring."""

    model_config = ConfigDict(extra="forbid")

    color_boldness: float
    formality: float
    price_tier: float
    silhouette_structure: float


class StyleProfile(BaseModel):
    dimensions: StyleDimensions
    evidence_ids: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str
    source: str
    label: str
    kind: Literal["aspirational", "purchase", "survey"]


class SurveyPrompt(BaseModel):
    id: str
    key: Literal["emotional_feedback", "usage_frequency", "purchase_motivation"]
    question: str
    options: list[str]


class PurchaseSurveyItem(BaseModel):
    id: str
    item_id: str
    item_name: str
    merchant: str
    price: float = Field(ge=0)
    currency: str = "USD"
    purchased_at: str
    returned: bool
    prompts: list[SurveyPrompt]


class GapDimension(BaseModel):
    key: str
    label: str
    aspiration: float
    behavior: float
    gap: float


class GroundedInsight(BaseModel):
    title: str
    body: str
    evidence_ids: list[str]


class GapReport(BaseModel):
    persona_id: str
    persona_name: str
    summary: str
    gap_score: int = Field(ge=0, le=100)
    dimensions: list[GapDimension]
    insights: list[GroundedInsight]
    evidence: list[EvidenceItem]


class CandidateItem(BaseModel):
    name: str
    price: float = Field(ge=0)
    dimensions: dict[str, float]


class SecondOpinionRequest(CandidateItem):
    pass


class OpinionDimension(BaseModel):
    label: str
    score: int = Field(ge=0, le=100)
    note: str


class SecondOpinionResponse(BaseModel):
    candidate_name: str
    reading: str
    dimensions: list[OpinionDimension]
    evidence_ids: list[str]


class DemoResponse(BaseModel):
    persona: dict[str, str]
    report: GapReport
    survey: list[PurchaseSurveyItem]
    candidate: CandidateItem


class ReportNarrative(BaseModel):
    summary: str
    insights: list[GroundedInsight]


class SecondOpinionNarrative(BaseModel):
    reading: str
    notes: list[str]


class AnalysisStage(BaseModel):
    name: str
    status: Literal["completed"] = "completed"
    detail: str


class ModelRuntime(BaseModel):
    provider: Literal["fixture", "openai"]
    specialist_model: str | None = None
    specialist_reasoning_effort: str | None = None
    synthesis_model: str | None = None
    synthesis_reasoning_effort: str | None = None
    trace_id: str | None = None


class AnalysisRun(BaseModel):
    data_mode: str
    analysis_mode: str
    model_runtime: ModelRuntime
    stages: list[AnalysisStage]
    report: GapReport
