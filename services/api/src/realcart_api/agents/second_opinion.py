"""Decision Reflection specialist definition."""

from typing import Any

from realcart_api.schemas import SecondOpinionNarrative


def create_second_opinion_agent(model: str = "gpt-5.6-sol") -> Any:
    from agents import Agent

    return Agent(
        name="Decision Reflection Agent",
        instructions=(
            "Reflect a user-supplied candidate against a precomputed RealCart shopping-pattern "
            "model. Explain how Style World alignment, spending patterns, returns, usage, and "
            "emotional feedback may be shaping this decision. The interpretation and decision "
            "always remain with the user. Never issue a buy/do-not-buy verdict or suggest other "
            "products."
        ),
        model=model,
        output_type=SecondOpinionNarrative,
    )
