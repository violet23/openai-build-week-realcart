"""Purchase-signal specialist definition."""

from typing import Any

from realcart_api.agents.model_config import create_model_settings
from realcart_api.schemas import StyleProfile
from realcart_api.settings import ReasoningEffort


def create_purchase_signal_agent(
    model: str = "gpt-5.6-terra", reasoning_effort: ReasoningEffort = "low"
) -> Any:
    from agents import Agent

    return Agent(
        name="Purchase Signal Agent",
        handoff_description="Extracts aesthetic-relevant purchase and survey signals.",
        instructions=(
            "Use only normalized receipt, return, and survey evidence. Exclude likely gifts "
            "and pure consumables. Separate logistical returns from taste-driven returns. "
            "Use exactly these dimensions: color_boldness, formality, price_tier, and "
            "silhouette_structure. Return values from 0 to 1 and cite only supplied "
            "evidence IDs. Never recommend products or invent evidence."
        ),
        model=model,
        model_settings=create_model_settings(reasoning_effort),
        output_type=StyleProfile,
    )
