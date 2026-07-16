"""Manager-style orchestration definition for future live report generation."""

from typing import Any

from realcart_api.agents.aspiration import create_aspiration_agent
from realcart_api.agents.purchase_signal import create_purchase_signal_agent
from realcart_api.schemas import ReportNarrative


def create_report_manager_agent(
    tagger_model: str = "gpt-5.6-terra", synthesis_model: str = "gpt-5.6-sol"
) -> Any:
    from agents import Agent

    aspiration = create_aspiration_agent(tagger_model)
    purchase = create_purchase_signal_agent(tagger_model)
    return Agent(
        name="Insight Report Manager",
        instructions=(
            "Call the two specialists for bounded tagging work. Application code calculates "
            "all numeric scores. Synthesize only grounded reflection prompts with evidence "
            "IDs. Do not produce purchase recommendations, rankings, or alternatives."
        ),
        model=synthesis_model,
        tools=[
            aspiration.as_tool(
                tool_name="analyze_aspirational_style",
                tool_description="Analyze saved-item evidence into a typed style profile.",
            ),
            purchase.as_tool(
                tool_name="analyze_purchase_signals",
                tool_description="Analyze normalized purchase and survey evidence.",
            ),
        ],
        output_type=ReportNarrative,
    )
