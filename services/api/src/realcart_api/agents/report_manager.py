"""Grounded synthesis agent used after deterministic scoring."""

from typing import Any

from realcart_api.agents.model_config import create_model_settings
from realcart_api.schemas import ReportNarrative
from realcart_api.settings import ReasoningEffort


def create_report_manager_agent(
    synthesis_model: str = "gpt-5.6-sol",
    reasoning_effort: ReasoningEffort = "medium",
) -> Any:
    from agents import Agent

    return Agent(
        name="Insight Report Manager",
        instructions=(
            "Synthesize the supplied saved-image style signals, repeated board themes, purchase "
            "patterns, and precomputed numeric Signal Distance into a personal shopping-pattern "
            "model and a short "
            "self-reflection report. "
            "Treat scenes and atmosphere as narrative context, not literal products the user "
            "wants. Cite only evidence IDs present in the input. Do not change or recalculate "
            "scores. Lead with observed shopping outcomes: keeps, returns, exchanges, prices, "
            "merchants, use, and feedback. Use saved images as a contextual style reference. "
            "Notice when a repeatedly saved style is also repeatedly bought and returned, but "
            "never generalize from one item. Treat both sources as partial evidence. Never imply "
            "saved images are an "
            "ideal or better self, or purchases are the authentic or real self. Purchases may "
            "reflect budget, fit, need, availability, and circumstance. Do not produce purchase "
            "recommendations, rankings, alternatives, "
            "psychological claims, or invented evidence."
        ),
        model=synthesis_model,
        model_settings=create_model_settings(reasoning_effort),
        output_type=ReportNarrative,
    )
