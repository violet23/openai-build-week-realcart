"""Aspirational-style specialist definition."""

from typing import Any

from realcart_api.schemas import StyleProfile


def create_aspiration_agent(model: str = "gpt-5.6-terra") -> Any:
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
        output_type=StyleProfile,
    )
