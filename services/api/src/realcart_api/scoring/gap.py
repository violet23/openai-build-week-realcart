"""Deterministic gap and Second Opinion calculations."""

from collections.abc import Mapping
from typing import Any

from realcart_api.schemas import (
    CandidateItem,
    EvidenceItem,
    GapDimension,
    GapReport,
    GroundedInsight,
    OpinionDimension,
    ReportNarrative,
    SecondOpinionResponse,
    StyleProfile,
)

DIMENSION_LABELS = {
    "color_boldness": "Color boldness",
    "formality": "Formality",
    "price_tier": "Price tier",
    "silhouette_structure": "Silhouette structure",
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _score_similarity(left: Mapping[str, float], right: Mapping[str, float]) -> int:
    shared = sorted(set(left) & set(right))
    if not shared:
        return 0
    distance = sum(abs(_clamp(left[key]) - _clamp(right[key])) for key in shared)
    return round((1 - distance / len(shared)) * 100)


def calculate_gap_dimensions(
    aspiration: StyleProfile, behavior: StyleProfile
) -> list[GapDimension]:
    shared = sorted(set(aspiration.dimensions) & set(behavior.dimensions))
    if not shared:
        raise ValueError("Aspiration and behavior profiles must share at least one dimension")

    return [
        GapDimension(
            key=key,
            label=DIMENSION_LABELS.get(key, key.replace("_", " ").title()),
            aspiration=round(_clamp(aspiration.dimensions[key]), 2),
            behavior=round(_clamp(behavior.dimensions[key]), 2),
            gap=round(abs(aspiration.dimensions[key] - behavior.dimensions[key]), 2),
        )
        for key in shared
    ]


def calculate_gap_score(dimensions: list[GapDimension]) -> int:
    if not dimensions:
        return 0
    return round(sum(dimension.gap for dimension in dimensions) / len(dimensions) * 100)


def _build_insights(
    dimensions: list[GapDimension], aspiration_ids: list[str], behavior_ids: list[str]
) -> list[GroundedInsight]:
    ranked = sorted(dimensions, key=lambda dimension: dimension.gap, reverse=True)
    insights: list[GroundedInsight] = []
    evidence_ids = [*aspiration_ids[:2], *behavior_ids[:2]]
    for dimension in ranked[:2]:
        direction = "higher" if dimension.aspiration > dimension.behavior else "lower"
        insights.append(
            GroundedInsight(
                title=f"Your saved {dimension.label.lower()} is {direction}",
                body=(
                    f"The {dimension.label.lower()} signal differs by "
                    f"{round(dimension.gap * 100)} points between saved and purchased items. "
                    "Treat this as a reflection prompt rather than a shopping verdict."
                ),
                evidence_ids=evidence_ids,
            )
        )
    return insights


def build_gap_report(
    payload: dict[str, Any],
    aspiration: StyleProfile | None = None,
    behavior: StyleProfile | None = None,
    narrative: ReportNarrative | None = None,
) -> GapReport:
    aspiration = aspiration or StyleProfile.model_validate(payload["aspiration"])
    behavior = behavior or StyleProfile.model_validate(payload["behavior"])
    dimensions = calculate_gap_dimensions(aspiration, behavior)
    persona: dict[str, str] = payload["persona"]
    evidence = [EvidenceItem.model_validate(item) for item in payload["evidence"]]
    known_evidence_ids = {item.id for item in evidence}
    insights = (
        narrative.insights
        if narrative is not None
        else _build_insights(dimensions, aspiration.evidence_ids, behavior.evidence_ids)
    )
    unknown_evidence_ids = {
        evidence_id
        for insight in insights
        for evidence_id in insight.evidence_ids
        if evidence_id not in known_evidence_ids
    }
    if unknown_evidence_ids:
        unknown = ", ".join(sorted(unknown_evidence_ids))
        raise ValueError(f"Narrative cited unknown evidence IDs: {unknown}")

    return GapReport(
        persona_id=persona["id"],
        persona_name=persona["display_name"],
        summary=(
            narrative.summary
            if narrative is not None
            else (
                "Your saved style is more structured and formal than the choices represented "
                "in this synthetic purchase history."
            )
        ),
        gap_score=calculate_gap_score(dimensions),
        dimensions=dimensions,
        insights=insights,
        evidence=evidence,
    )


def _spend_fit(price: float, spend_range: list[float]) -> int:
    lower, upper = spend_range
    if lower <= price <= upper:
        return 100
    distance = lower - price if price < lower else price - upper
    scale = max(upper - lower, 1)
    return round(max(0, 100 - distance / scale * 100))


def build_second_opinion(
    payload: dict[str, Any], candidate: CandidateItem
) -> SecondOpinionResponse:
    aspiration = StyleProfile.model_validate(payload["aspiration"])
    behavior: dict[str, Any] = payload["behavior"]
    aesthetic_fit = _score_similarity(candidate.dimensions, aspiration.dimensions)
    spend_fit = _spend_fit(candidate.price, behavior["typical_spend_range"])
    regret_similarity = _score_similarity(candidate.dimensions, behavior["regret_profile"])

    return SecondOpinionResponse(
        candidate_name=candidate.name,
        reading=(
            "This item resembles the structured style in the saved profile, sits above the "
            "synthetic usual spend range, and overlaps with a prior regret pattern. "
            "Those are signals to consider; the interpretation and decision remain yours."
        ),
        dimensions=[
            OpinionDimension(
                label="Aesthetic fit",
                score=aesthetic_fit,
                note="Similarity to the aspirational style profile.",
            ),
            OpinionDimension(
                label="Spend-range fit",
                score=spend_fit,
                note="Position relative to the observed synthetic spend range.",
            ),
            OpinionDimension(
                label="Regret-pattern similarity",
                score=regret_similarity,
                note="Higher means more overlap with previously regretted style signals.",
            ),
        ],
        evidence_ids=[*aspiration.evidence_ids[:2], "survey-01"],
    )
