"""Shared OpenAI model settings for RealCart agents."""

from typing import TYPE_CHECKING

from realcart_api.settings import ReasoningEffort

if TYPE_CHECKING:
    from agents import ModelSettings


def create_model_settings(reasoning_effort: ReasoningEffort) -> "ModelSettings":
    """Build privacy-conscious settings for one structured GPT-5.6 response."""

    from agents import ModelSettings
    from openai.types.shared import Reasoning

    return ModelSettings(
        reasoning=Reasoning(effort=reasoning_effort),
        verbosity="low",
        include_usage=True,
        store=False,
    )
