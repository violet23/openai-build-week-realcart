from typing import Any

from realcart_api.schemas import StyleProfile
from realcart_api.scoring.gap import (
    aggregate_style_items,
    build_gap_report,
    calculate_gap_dimensions,
    calculate_gap_score,
)


def test_gap_score_is_deterministic() -> None:
    aspiration = StyleProfile(
        dimensions={
            "color_warmth": 0.7,
            "color_saturation": 0.7,
            "visual_contrast": 0.7,
            "structure": 0.7,
            "texture_naturalness": 0.7,
            "ornamentation": 0.7,
            "polish": 0.7,
        }
    )
    behavior = StyleProfile(
        dimensions={
            "color_warmth": 0.4,
            "color_saturation": 0.4,
            "visual_contrast": 0.4,
            "structure": 0.4,
            "texture_naturalness": 0.4,
            "ornamentation": 0.4,
            "polish": 0.4,
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
        "color_warmth": 0.85,
        "color_saturation": 0.34,
        "visual_contrast": 0.49,
        "structure": 0.63,
        "texture_naturalness": 0.85,
        "ornamentation": 0.49,
        "polish": 0.77,
    }
    assert behavior.dimensions.model_dump() == {
        "color_warmth": 0.15,
        "color_saturation": 0.33,
        "visual_contrast": 0.47,
        "structure": 0.25,
        "texture_naturalness": 0.25,
        "ornamentation": 0.18,
        "polish": 0.17,
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
    assert [theme.name for theme in report.vision_themes] == [
        "Calm",
        "Warm",
        "Natural",
        "Polished",
    ]
    assert report.insights
    assert all(set(insight.evidence_ids) <= known_ids for insight in report.insights)
