"""Aspirational-style specialist definition."""

from typing import Any

from realcart_api.agents.model_config import create_model_settings
from realcart_api.schemas import StyleProfile
from realcart_api.settings import ReasoningEffort


def create_aspiration_agent(
    model: str = "gpt-5.6-terra", reasoning_effort: ReasoningEffort = "low"
) -> Any:
    from agents import Agent

    return Agent(
        name="Aspirational Style Agent",
        handoff_description="Tags saved images on RealCart's shared style taxonomy.",
        instructions=(
            "Analyze only the supplied Pinterest or fixture evidence. Use exactly these "
            "dimensions: color_boldness, formality, price_tier, and silhouette_structure. "
            "Return values from 0 to 1 and cite only supplied evidence IDs. Do not infer "
            "purchases, recommend products, or invent evidence."
        ),
        model=model,
        model_settings=create_model_settings(reasoning_effort),
        output_type=StyleProfile,
    )
