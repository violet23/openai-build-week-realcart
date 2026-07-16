from realcart_api.schemas import CandidateItem, StyleProfile
from realcart_api.scoring.gap import (
    build_gap_report,
    build_second_opinion,
    calculate_gap_dimensions,
    calculate_gap_score,
)


def test_gap_score_is_deterministic() -> None:
    aspiration = StyleProfile(dimensions={"formality": 0.8, "price_tier": 0.7})
    behavior = StyleProfile(dimensions={"formality": 0.4, "price_tier": 0.5})
    dimensions = calculate_gap_dimensions(aspiration, behavior)

    assert calculate_gap_score(dimensions) == 30


def test_fixture_report_is_grounded(fixture_payload: dict[str, object]) -> None:
    report = build_gap_report(fixture_payload)
    known_ids = {item.id for item in report.evidence}

    assert 0 <= report.gap_score <= 100
    assert report.insights
    assert all(set(insight.evidence_ids) <= known_ids for insight in report.insights)


def test_second_opinion_avoids_verdict(fixture_payload: dict[str, object]) -> None:
    candidate = CandidateItem.model_validate(fixture_payload["candidate"])
    opinion = build_second_opinion(fixture_payload, candidate)
    lowered = opinion.reading.lower()

    assert "recommend" not in lowered
    assert "you should buy" not in lowered
    assert len(opinion.dimensions) == 3
