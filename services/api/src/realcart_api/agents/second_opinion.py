"""Second Opinion specialist definition."""

from typing import Any

from realcart_api.schemas import SecondOpinionNarrative


def create_second_opinion_agent(model: str = "gpt-5.6-sol") -> Any:
    from agents import Agent

    return Agent(
        name="Second Opinion Agent",
        instructions=(
            "Read a user-supplied candidate against a precomputed RealCart profile. Explain "
            "aesthetic fit, spend-range position, and regret-pattern similarity. The decision "
            "always remains with the user. Never issue a buy/do-not-buy verdict or suggest "
            "other products."
        ),
        model=model,
        output_type=SecondOpinionNarrative,
    )
