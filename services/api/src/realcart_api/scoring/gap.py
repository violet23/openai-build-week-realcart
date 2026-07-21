"""Deterministic Style Gap calculations."""

from typing import Any, Literal

from realcart_api.schemas import (
    EvidenceItem,
    GapDimension,
    GapReport,
    GeneratedPortrait,
    GroundedInsight,
    ReportNarrative,
    ScoreProvenance,
    StyleDimensions,
    StyleProfile,
    StyleSignalItem,
    VisionTheme,
)

DIMENSION_LABELS = {
    "color_warmth": "Color warmth",
    "color_saturation": "Color saturation",
    "visual_contrast": "Visual contrast",
    "structure": "Structure",
    "texture_naturalness": "Natural texture",
    "ornamentation": "Ornamentation",
    "polish": "Polish",
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def aggregate_style_items(
    raw_items: list[dict[str, Any]], *, exclude_returned: bool = False
) -> StyleProfile:
    """Build a profile from traceable item-level fixture scores."""

    items = [StyleSignalItem.model_validate(item) for item in raw_items]
    included = [item for item in items if not (exclude_returned and item.returned)]
    if not included:
        raise ValueError("At least one eligible style item is required")
    total_weight = sum(item.confidence for item in included)
    if total_weight <= 0:
        raise ValueError("Style item confidence must include a positive value")

    dimensions = {
        key: round(
            sum(
                getattr(item.dimensions, key) * item.confidence for item in included
            )
            / total_weight,
            2,
        )
        for key in StyleDimensions.model_fields
    }
    return StyleProfile(
        dimensions=StyleDimensions.model_validate(dimensions),
        evidence_ids=[item.id for item in included],
    )


def aggregate_vision_themes(raw_items: list[dict[str, Any]]) -> list[VisionTheme]:
    """Keep repeated board-level themes without forcing them into the Style Gap."""

    items = [StyleSignalItem.model_validate(item) for item in raw_items]
    total_confidence = sum(item.confidence for item in items)
    if total_confidence <= 0:
        return []

    support: dict[str, list[StyleSignalItem]] = {}
    for item in items:
        for theme in set(item.themes):
            support.setdefault(theme, []).append(item)

    themes = [
        VisionTheme(
            name=name.replace("_", " ").title(),
            strength=round(
                sum(item.confidence for item in supporting_items) / total_confidence,
                2,
            ),
            confidence=round(
                sum(item.confidence for item in supporting_items)
                / len(supporting_items),
                2,
            ),
            evidence_ids=[item.id for item in supporting_items],
        )
        for name, supporting_items in support.items()
        if len(supporting_items) >= 2
    ]
    return sorted(themes, key=lambda theme: (-theme.strength, theme.name))


def calculate_gap_dimensions(
    aspiration: StyleProfile, behavior: StyleProfile
) -> list[GapDimension]:
    aspiration_dimensions = aspiration.dimensions.model_dump()
    behavior_dimensions = behavior.dimensions.model_dump()
    shared = sorted(set(aspiration_dimensions) & set(behavior_dimensions))
    if not shared:
        raise ValueError("Style World and Purchase Reality must share at least one dimension")

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
                title=f"Your Style World {dimension.label.lower()} is {direction}",
                body=(
                    f"The {dimension.label.lower()} signal differs by "
                    f"{round(dimension.gap * 100)} points between your Style World "
                    "and kept Purchase Reality. "
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
    vision_themes: list[VisionTheme] | None = None,
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
    vision_themes = vision_themes or aggregate_vision_themes(
        payload["aspirational_items"]
    )
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
    unknown_evidence_ids.update(
        evidence_id
        for theme in vision_themes
        for evidence_id in theme.evidence_ids
        if evidence_id not in known_evidence_ids
    )
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
                "Your Style World repeatedly points to a warm, natural, calm fashion life, "
                "while your kept Purchase Reality leans more practical, cooler, and less "
                "polished."
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
        vision_themes=vision_themes,
        portraits=[
            GeneratedPortrait.model_validate(item)
            for item in payload.get("portraits", [])
        ],
    )
