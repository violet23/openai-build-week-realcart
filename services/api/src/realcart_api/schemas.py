"""Typed contracts shared by connectors, scoring, agents, and API routes."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StyleDimensions(BaseModel):
    """Fixed taxonomy shared by specialist agents and deterministic scoring."""

    model_config = ConfigDict(extra="forbid")

    color_warmth: float = Field(ge=0, le=1)
    color_saturation: float = Field(ge=0, le=1)
    visual_contrast: float = Field(ge=0, le=1)
    structure: float = Field(ge=0, le=1)
    texture_naturalness: float = Field(ge=0, le=1)
    ornamentation: float = Field(ge=0, le=1)
    polish: float = Field(ge=0, le=1)


class StyleProfile(BaseModel):
    dimensions: StyleDimensions
    evidence_ids: list[str] = Field(default_factory=list)


class VisionTheme(BaseModel):
    name: str
    strength: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]


class VisionProfile(StyleProfile):
    themes: list[VisionTheme]


class ImageAsset(BaseModel):
    id: str
    source: Literal["fixture", "gmail", "pinterest", "generated"]
    image_url: str
    alt_text: str
    mime_type: str


class StyleSignalItem(BaseModel):
    id: str
    source: str
    label: str
    dimensions: StyleDimensions
    returned: bool = False
    confidence: float = Field(default=1, ge=0, le=1)
    intent_type: Literal[
        "atmosphere_reference", "scene_reference", "product_reference", "mixed"
    ] | None = None
    literal_content: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    visual_evidence: list[str] = Field(default_factory=list)
    image: ImageAsset | None = None


class EvidenceItem(BaseModel):
    id: str
    source: str
    label: str
    kind: Literal["aspirational", "purchase", "survey"]


class SurveyPrompt(BaseModel):
    id: str
    key: Literal[
        "emotional_feedback",
        "usage_frequency",
        "purchase_motivation",
        "return_reason",
        "return_sentiment",
    ]
    question: str
    options: list[str]


class PurchaseSurveyItem(BaseModel):
    id: str
    item_id: str
    item_name: str
    merchant: str
    price: float | None = Field(default=None, ge=0)
    currency: str = "USD"
    purchased_at: str
    returned: bool
    image: ImageAsset | None = None
    prompts: list[SurveyPrompt]
    comment_prompt: str


class SurveyAnswer(BaseModel):
    item_id: str
    values: dict[str, str]
    notes: str = Field(default="", max_length=500)


class AnalysisRequest(BaseModel):
    answers: list[SurveyAnswer] = Field(default_factory=list)


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


class ScoreProvenance(BaseModel):
    aspirational_item_count: int = Field(ge=0)
    purchase_item_count: int = Field(ge=0)
    kept_purchase_count: int = Field(ge=0)
    returned_item_count: int = Field(ge=0)
    profile_method: Literal["fixture_item_average", "agent_profiles"]


class GeneratedPortrait(BaseModel):
    kind: Literal["style_world", "purchase_reality"]
    title: str
    image: ImageAsset
    evidence_ids: list[str]
    model: str
    generation_mode: Literal["fixture", "openai"]


class GapReport(BaseModel):
    persona_id: str
    persona_name: str
    summary: str
    gap_score: int = Field(ge=0, le=100)
    dimensions: list[GapDimension]
    insights: list[GroundedInsight]
    evidence: list[EvidenceItem]
    score_provenance: ScoreProvenance
    vision_themes: list[VisionTheme]
    portraits: list[GeneratedPortrait] = Field(default_factory=list)


class DemoResponse(BaseModel):
    persona: dict[str, str]
    report: GapReport
    survey: list[PurchaseSurveyItem]


class ReportNarrative(BaseModel):
    summary: str
    insights: list[GroundedInsight]


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
    image_model: str | None = None
    trace_id: str | None = None


class SourceConnection(BaseModel):
    source: Literal["gmail", "pinterest"]
    configured: bool
    connected: bool
    environment: Literal["gmail", "sandbox"]
    connect_url: str


class ConnectionOverview(BaseModel):
    data_mode: str
    sources: list[SourceConnection]


class AnalysisRun(BaseModel):
    data_mode: str
    analysis_mode: str
    model_runtime: ModelRuntime
    stages: list[AnalysisStage]
    report: GapReport
