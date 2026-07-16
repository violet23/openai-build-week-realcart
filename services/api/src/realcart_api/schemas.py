"""Typed contracts shared by connectors, scoring, agents, and API routes."""

from typing import Literal

from pydantic import BaseModel, Field


class StyleProfile(BaseModel):
    dimensions: dict[str, float]
    evidence_ids: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    id: str
    source: str
    label: str
    kind: Literal["aspirational", "purchase", "survey"]


class SurveyQuestion(BaseModel):
    id: str
    item_id: str
    question: str
    options: list[str]


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
    survey: list[SurveyQuestion]
    candidate: CandidateItem


class ReportNarrative(BaseModel):
    summary: str
    insights: list[GroundedInsight]


class SecondOpinionNarrative(BaseModel):
    reading: str
    notes: list[str]
