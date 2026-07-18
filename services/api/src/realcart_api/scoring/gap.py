"""Deterministic gap and Second Opinion calculations."""

from collections.abc import Mapping
from typing import Any, Literal

from realcart_api.schemas import (
    CandidateItem,
    EvidenceItem,
    GapDimension,
    GapReport,
    GroundedInsight,
    OpinionDimension,
    ReportNarrative,
    ScoreProvenance,
    SecondOpinionResponse,
    StyleDimensions,
    StyleProfile,
    StyleSignalItem,
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


def aggregate_style_items(
    raw_items: list[dict[str, Any]], *, exclude_returned: bool = False
) -> StyleProfile:
    """Build a profile from traceable item-level fixture scores."""

    items = [StyleSignalItem.model_validate(item) for item in raw_items]
    included = [item for item in items if not (exclude_returned and item.returned)]
    if not included:
        raise ValueError("At least one eligible style item is required")

    dimensions = {
        key: round(
            sum(getattr(item.dimensions, key) for item in included) / len(included),
            2,
        )
        for key in StyleDimensions.model_fields
    }
    return StyleProfile(
        dimensions=StyleDimensions.model_validate(dimensions),
        evidence_ids=[item.id for item in included],
    )


def calculate_gap_dimensions(
    aspiration: StyleProfile, behavior: StyleProfile
) -> list[GapDimension]:
    aspiration_dimensions = aspiration.dimensions.model_dump()
    behavior_dimensions = behavior.dimensions.model_dump()
    shared = sorted(set(aspiration_dimensions) & set(behavior_dimensions))
    if not shared:
        raise ValueError("Aspiration and behavior profiles must share at least one dimension")

    return [
        GapDimension(
            key=key,
            label=DIMENSION_LABELS.get(key, key.replace("_", " ").title()),
            aspiration=round(_clamp(aspiration_dimensions[key]), 2),
            behavior=round(_clamp(behavior_dimensions[key]), 2),
            gap=round(abs(aspiration_dimensions[key] - behavior_dimensions[key]), 2),
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
    profile_method: Literal["fixture_item_average", "agent_profiles"] = (
        "fixture_item_average"
        if aspiration is None and behavior is None
        else "agent_profiles"
    )
    aspiration = aspiration or aggregate_style_items(payload["aspirational_items"])
    behavior = behavior or aggregate_style_items(
        payload["purchase_items"], exclude_returned=True
    )
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
        score_provenance=ScoreProvenance(
            aspirational_item_count=len(payload["aspirational_items"]),
            purchase_item_count=len(payload["purchase_items"]),
            kept_purchase_count=sum(
                not bool(item.get("returned")) for item in payload["purchase_items"]
            ),
            returned_item_count=sum(
                bool(item.get("returned")) for item in payload["purchase_items"]
            ),
            profile_method=profile_method,
        ),
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
    aspiration = aggregate_style_items(payload["aspirational_items"])
    kept_purchases = [
        item for item in payload["purchase_items"] if not bool(item.get("returned"))
    ]
    returned_purchases = [
        item for item in payload["purchase_items"] if bool(item.get("returned"))
    ]
    prices = [float(item["price"]) for item in kept_purchases]
    if not prices or not returned_purchases:
        raise ValueError("Second Opinion requires kept and returned purchase fixtures")
    regret_profile = aggregate_style_items(returned_purchases)
    aesthetic_fit = _score_similarity(
        candidate.dimensions, aspiration.dimensions.model_dump()
    )
    spend_fit = _spend_fit(candidate.price, [min(prices), max(prices)])
    regret_similarity = _score_similarity(
        candidate.dimensions, regret_profile.dimensions.model_dump()
    )

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
