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
        name="Purchase Patterns Agent",
        handoff_description="Builds purchase patterns from receipts, returns, use, and feedback.",
        instructions=(
            "Build the user's purchase-pattern profile using only normalized purchase history, "
            "return, usage, and emotional-feedback evidence. Exclude likely gifts and pure "
            "consumables. "
            "Treat purchases, keeps, returns, exchanges, prices, merchants, use, and feedback as "
            "the primary record of observed shopping outcomes. Separate logistical returns from "
            "taste-driven returns. Look for repeated brand, category, price, and style patterns, "
            "but require multiple records before calling something a preference. Purchases are "
            "also shaped by budget, need, fit, availability, timing, and circumstance; never call "
            "them the real or authentic self. Use the same transferable visual "
            "dimensions as the Saved Style Signals Agent: "
            "color_warmth, color_saturation, visual_contrast, structure, "
            "texture_naturalness, ornamentation, and polish. Return values from 0 to 1 and "
            "cite only supplied evidence IDs. Never recommend products or invent evidence."
        ),
        model=model,
        model_settings=create_model_settings(reasoning_effort),
        output_type=StyleProfile,
    )
