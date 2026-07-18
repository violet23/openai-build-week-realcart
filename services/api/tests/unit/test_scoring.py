from typing import Any

from realcart_api.schemas import CandidateItem, StyleProfile
from realcart_api.scoring.gap import (
    aggregate_style_items,
    build_gap_report,
    build_second_opinion,
    calculate_gap_dimensions,
    calculate_gap_score,
)


def test_gap_score_is_deterministic() -> None:
    aspiration = StyleProfile(
        dimensions={
            "color_boldness": 0.7,
            "formality": 0.8,
            "price_tier": 0.7,
            "silhouette_structure": 0.8,
        }
    )
    behavior = StyleProfile(
        dimensions={
            "color_boldness": 0.4,
            "formality": 0.4,
            "price_tier": 0.5,
            "silhouette_structure": 0.5,
        }
    )
    dimensions = calculate_gap_dimensions(aspiration, behavior)

    assert calculate_gap_score(dimensions) == 30


def test_fixture_profiles_are_derived_from_item_records(
    fixture_payload: dict[str, Any],
) -> None:
    aspiration = aggregate_style_items(fixture_payload["aspirational_items"])
    behavior = aggregate_style_items(
        fixture_payload["purchase_items"], exclude_returned=True
    )

    assert aspiration.dimensions.model_dump() == {
        "color_boldness": 0.72,
        "formality": 0.81,
        "price_tier": 0.76,
        "silhouette_structure": 0.84,
    }
    assert behavior.dimensions.model_dump() == {
        "color_boldness": 0.44,
        "formality": 0.39,
        "price_tier": 0.47,
        "silhouette_structure": 0.36,
    }
    assert behavior.evidence_ids == ["purchase-01", "purchase-02", "purchase-03"]


def test_fixture_report_is_grounded(fixture_payload: dict[str, Any]) -> None:
    report = build_gap_report(fixture_payload)
    known_ids = {item.id for item in report.evidence}

    assert report.gap_score == 37
    assert report.score_provenance.aspirational_item_count == 4
    assert report.score_provenance.purchase_item_count == 4
    assert report.score_provenance.kept_purchase_count == 3
    assert report.score_provenance.returned_item_count == 1
    assert report.score_provenance.profile_method == "fixture_item_average"
    assert report.insights
    assert all(set(insight.evidence_ids) <= known_ids for insight in report.insights)


def test_second_opinion_avoids_verdict(fixture_payload: dict[str, Any]) -> None:
    candidate = CandidateItem.model_validate(fixture_payload["candidate"])
    opinion = build_second_opinion(fixture_payload, candidate)
    lowered = opinion.reading.lower()

    assert "recommend" not in lowered
    assert "you should buy" not in lowered
    assert len(opinion.dimensions) == 3
