"""Grounded synthesis agent used after deterministic scoring."""

from typing import Any

from realcart_api.schemas import ReportNarrative


def create_report_manager_agent(synthesis_model: str = "gpt-5.6-sol") -> Any:
    from agents import Agent

    return Agent(
        name="Insight Report Manager",
        instructions=(
            "Synthesize the supplied specialist profiles and precomputed numeric gap scores "
            "into a short self-reflection report. Cite only evidence IDs present in the "
            "input. Do not change or recalculate scores. Do not produce purchase "
            "recommendations, rankings, alternatives, or invented evidence."
        ),
        model=synthesis_model,
        output_type=ReportNarrative,
    )
