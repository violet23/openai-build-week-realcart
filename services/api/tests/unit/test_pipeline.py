from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any

import agents
import pytest

from realcart_api.output import render_markdown
from realcart_api.pipeline import PipelineConfigurationError, run_pipeline
from realcart_api.schemas import GroundedInsight, ReportNarrative, StyleProfile


@pytest.mark.asyncio
async def test_fixture_pipeline_is_complete_and_credential_free() -> None:
    run = await run_pipeline(data_mode="fixture", analysis_mode="fixture")

    assert run.report.gap_score > 0
    assert [stage.name for stage in run.stages] == [
        "fetch",
        "specialist_analysis",
        "scoring",
        "synthesis",
    ]
    assert run.model_runtime.provider == "fixture"
    assert run.model_runtime.specialist_model is None


@pytest.mark.asyncio
async def test_agent_mode_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(PipelineConfigurationError, match="OPENAI_API_KEY"):
        await run_pipeline(data_mode="fixture", analysis_mode="agents")


@pytest.mark.asyncio
async def test_agent_mode_uses_real_gpt_5_6_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, Any]] = []

    async def fake_run(agent: Any, _input: str, *, run_config: Any) -> Any:
        calls.append((agent, run_config))
        if agent.name == "Aspirational Style Agent":
            output: Any = StyleProfile(
                dimensions={
                    "color_boldness": 0.72,
                    "formality": 0.81,
                    "price_tier": 0.76,
                    "silhouette_structure": 0.84,
                },
                evidence_ids=["pin-01", "pin-02"],
            )
        elif agent.name == "Purchase Signal Agent":
            output = StyleProfile(
                dimensions={
                    "color_boldness": 0.44,
                    "formality": 0.39,
                    "price_tier": 0.47,
                    "silhouette_structure": 0.36,
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
    assert run.model_runtime.specialist_model == "gpt-5.6-terra"
    assert run.model_runtime.synthesis_model == "gpt-5.6-sol"
    assert [agent.name for agent, _config in calls] == [
        "Aspirational Style Agent",
        "Purchase Signal Agent",
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

    assert "# RealCart Insight Report" in rendered
    assert "Evidence:" in rendered
    assert "## Runtime" in rendered
    assert "## Pipeline" in rendered
