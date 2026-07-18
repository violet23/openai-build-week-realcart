"""Vision-board specialist definition."""

from typing import Any

from realcart_api.agents.model_config import create_model_settings
from realcart_api.schemas import VisionProfile
from realcart_api.settings import ReasoningEffort


def create_aspiration_agent(
    model: str = "gpt-5.6-terra", reasoning_effort: ReasoningEffort = "low"
) -> Any:
    from agents import Agent

    return Agent(
        name="Style World Agent",
        handoff_description="Interprets the repeated fashion world across saved images.",
        instructions=(
            "Build the user's Style World. Treat Pinterest as a vision board, not a wishlist. "
            "Analyze literal content, scene, palette, material, form, and atmosphere across "
            "the supplied items, focusing on signals relevant to fashion and its surrounding "
            "lifestyle. Do not assume a saved object is something the user wants to buy. Use "
            "exactly these "
            "transferable dimensions: color_warmth, color_saturation, visual_contrast, "
            "structure, texture_naturalness, ornamentation, and polish. Return values from "
            "0 to 1. Include only themes repeated across multiple pins, with confidence and "
            "supporting evidence IDs. Cite only supplied IDs. Never infer purchases, identity, "
            "or psychological traits; never recommend products or invent evidence."
        ),
        model=model,
        model_settings=create_model_settings(reasoning_effort),
        output_type=VisionProfile,
    )
