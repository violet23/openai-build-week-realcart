import pytest

from realcart_api.output import render_markdown
from realcart_api.pipeline import PipelineConfigurationError, run_pipeline


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


@pytest.mark.asyncio
async def test_agent_mode_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(PipelineConfigurationError, match="OPENAI_API_KEY"):
        await run_pipeline(data_mode="fixture", analysis_mode="agents")


@pytest.mark.asyncio
async def test_markdown_output_contains_evidence_and_pipeline() -> None:
    run = await run_pipeline(data_mode="fixture", analysis_mode="fixture")
    rendered = render_markdown(run)

    assert "# RealCart Insight Report" in rendered
    assert "Evidence:" in rendered
    assert "## Pipeline" in rendered
