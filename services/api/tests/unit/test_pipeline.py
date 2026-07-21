from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any

import agents
import httpx
import openai
import pytest
from agents import AgentOutputSchema

from realcart_api.output import render_markdown
from realcart_api.pipeline import (
    PipelineConfigurationError,
    _model_execution_error_message,
    _multimodal_input,
    run_pipeline,
)
from realcart_api.schemas import (
    GroundedInsight,
    ReportNarrative,
    StyleProfile,
    VisionProfile,
    VisionTheme,
)


def test_multimodal_input_pairs_images_with_evidence_ids() -> None:
    result = _multimodal_input(
        task="Analyze images",
        evidence=[{"id": "pin-live", "kind": "aspirational"}],
        items=[
            {
                "id": "pin-live",
                "label": "Warm street scene",
                "dimensions": {"fixture_only": 1},
                "_image_data_url": "data:image/jpeg;base64,YWJj",
            }
        ],
        extra={},
    )

    content = result[0]["content"]
    assert [item["type"] for item in content] == [
        "input_text",
        "input_text",
        "input_image",
    ]
    assert content[1]["text"] == "Image evidence for item pin-live"
    assert content[2]["image_url"].startswith("data:image/jpeg;base64,")


@pytest.mark.asyncio
async def test_fixture_pipeline_is_complete_and_credential_free() -> None:
    run = await run_pipeline(data_mode="fixture", analysis_mode="fixture")

    assert run.report.gap_score > 0
    assert [stage.name for stage in run.stages] == [
        "fetch",
        "specialist_analysis",
        "scoring",
        "synthesis",
        "visual_generation",
    ]
    assert run.model_runtime.provider == "fixture"
    assert run.model_runtime.specialist_model is None


@pytest.mark.asyncio
async def test_agent_mode_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(PipelineConfigurationError, match="OPENAI_API_KEY"):
        await run_pipeline(data_mode="fixture", analysis_mode="agents")


def test_quota_error_message_is_specific_and_safe() -> None:
    response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://api.openai.com/v1/responses"),
    )
    error = openai.RateLimitError(
        "quota reached",
        response=response,
        body={"code": "insufficient_quota", "type": "insufficient_quota"},
    )

    message = _model_execution_error_message(error)

    assert "insufficient_quota" in message
    assert "project budget is above $0" in message
    assert "quota reached" not in message


def test_agent_outputs_have_strict_json_schemas() -> None:
    style_schema = AgentOutputSchema(VisionProfile).json_schema()
    narrative_schema = AgentOutputSchema(ReportNarrative).json_schema()

    dimensions_schema = style_schema["$defs"]["StyleDimensions"]
    assert dimensions_schema["additionalProperties"] is False
    assert set(dimensions_schema["required"]) == {
        "color_warmth",
        "color_saturation",
        "visual_contrast",
        "structure",
        "texture_naturalness",
        "ornamentation",
        "polish",
    }
    assert narrative_schema["additionalProperties"] is False


@pytest.mark.asyncio
async def test_agent_mode_uses_real_gpt_5_6_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, Any]] = []

    async def fake_run(agent: Any, _input: Any, *, run_config: Any) -> Any:
        calls.append((agent, run_config))
        if agent.name == "Style World Agent":
            output: Any = VisionProfile(
                dimensions={
                    "color_warmth": 0.85,
                    "color_saturation": 0.34,
                    "visual_contrast": 0.49,
                    "structure": 0.63,
                    "texture_naturalness": 0.85,
                    "ornamentation": 0.49,
                    "polish": 0.77,
                },
                evidence_ids=["pin-01", "pin-02"],
                themes=[
                    VisionTheme(
                        name="Warm natural calm",
                        strength=0.8,
                        confidence=0.9,
                        evidence_ids=["pin-01", "pin-02"],
                    )
                ],
            )
        elif agent.name == "Purchase Reality Agent":
            output = StyleProfile(
                dimensions={
                    "color_warmth": 0.38,
                    "color_saturation": 0.38,
                    "visual_contrast": 0.44,
                    "structure": 0.32,
                    "texture_naturalness": 0.48,
                    "ornamentation": 0.2,
                    "polish": 0.26,
                },
                evidence_ids=["purchase-01", "survey-01"],
            )
        else:
            output = ReportNarrative(
                summary="A grounded synthesis from the two specialist profiles.",
                insights=[
                    GroundedInsight(
                        title="Structure differs",
                        body="The saved and observed structure signals differ.",
                        evidence_ids=["pin-01", "purchase-01"],
                    )
                ],
            )
        return SimpleNamespace(final_output=output)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(agents.Runner, "run", fake_run)
    monkeypatch.setattr(agents, "trace", lambda *_args, **_kwargs: nullcontext())

    run = await run_pipeline(data_mode="fixture", analysis_mode="agents")

    assert run.model_runtime.provider == "openai"
    assert run.report.score_provenance.profile_method == "agent_profiles"
    assert run.model_runtime.specialist_model == "gpt-5.6-terra"
    assert run.model_runtime.synthesis_model == "gpt-5.6-sol"
    assert [agent.name for agent, _config in calls] == [
        "Style World Agent",
        "Purchase Reality Agent",
        "Insight Report Manager",
    ]
    assert all(config.trace_include_sensitive_data is False for _agent, config in calls)
    assert all(agent.model_settings.store is False for agent, _config in calls)
    assert calls[0][0].model_settings.reasoning.effort == "low"
    assert calls[2][0].model_settings.reasoning.effort == "medium"


@pytest.mark.asyncio
async def test_markdown_output_contains_evidence_and_pipeline() -> None:
    run = await run_pipeline(data_mode="fixture", analysis_mode="fixture")
    rendered = render_markdown(run)

    assert "# RealCart Shopping-Pattern Report" in rendered
    assert "Evidence:" in rendered
    assert "## Runtime" in rendered
    assert "## Style-gap provenance" in rendered
    assert "## Style World themes" in rendered
    assert "## Pipeline" in rendered
