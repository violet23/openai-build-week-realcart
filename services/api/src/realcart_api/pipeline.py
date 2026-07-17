"""Backend-first orchestration for fetching, analysis, scoring, and synthesis."""

from __future__ import annotations

import asyncio
import json
from os import getenv
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from realcart_api.agents.aspiration import create_aspiration_agent
from realcart_api.agents.purchase_signal import create_purchase_signal_agent
from realcart_api.agents.report_manager import create_report_manager_agent
from realcart_api.connectors import FixtureConnector
from realcart_api.connectors.base import SignalConnector
from realcart_api.schemas import (
    AnalysisRun,
    AnalysisStage,
    ModelRuntime,
    ReportNarrative,
    StyleProfile,
)
from realcart_api.scoring import build_gap_report
from realcart_api.settings import settings

if TYPE_CHECKING:
    from agents import RunConfig


class PipelineConfigurationError(RuntimeError):
    """Raised when a requested pipeline mode cannot run safely."""


class PipelineExecutionError(RuntimeError):
    """Raised when a configured external model run fails."""


def _openai_error_code(error: Exception) -> str | None:
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return None
    details = body.get("error", body)
    if not isinstance(details, dict):
        return None
    for field in ("code", "type"):
        value = details.get(field)
        if isinstance(value, str):
            return value
    return None


def _model_execution_error_message(error: Exception) -> str:
    """Return an actionable external-error message without leaking request contents."""

    from openai import (
        APIConnectionError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
    )

    code = _openai_error_code(error)
    if isinstance(error, AuthenticationError):
        return (
            "OpenAI rejected the API key. Confirm it is active and belongs to the "
            "intended Platform project."
        )
    if isinstance(error, RateLimitError):
        if code == "insufficient_quota":
            return (
                "OpenAI API returned insufficient_quota. Add API credits to the "
                "organization that owns this key and make sure the project budget is above $0."
            )
        return "OpenAI API rate limit reached. Wait briefly, then retry the agent run."
    if isinstance(error, (PermissionDeniedError, NotFoundError)):
        return (
            "This OpenAI Platform project cannot access one of the configured models "
            f"({settings.tagger_model}, {settings.synthesis_model})."
        )
    if isinstance(error, BadRequestError):
        suffix = f" ({code})" if code else ""
        return (
            f"OpenAI rejected the GPT-5.6 request{suffix}. Check the configured model "
            "parameters and structured-output schema."
        )
    if isinstance(error, APIConnectionError):
        return "Could not connect to the OpenAI API. Check the network, proxy, and firewall."
    return (
        "GPT-5.6 agent execution failed "
        f"({type(error).__name__}). Inspect the agent trace for this run."
    )


def _connector_for(data_mode: str) -> SignalConnector:
    if data_mode == "fixture":
        return FixtureConnector()
    if data_mode == "live":
        raise PipelineConfigurationError(
            "Live connectors are not enabled yet. Use DATA_MODE=fixture until Pinterest "
            "Sandbox and Gmail OAuth are implemented."
        )
    raise PipelineConfigurationError(f"Unsupported DATA_MODE: {data_mode}")


def _evidence_for(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [item for item in payload["evidence"] if item["kind"] == kind]


async def _run_specialist_agents(
    payload: dict[str, Any], run_config: RunConfig
) -> tuple[StyleProfile, StyleProfile]:
    if not getenv("OPENAI_API_KEY"):
        raise PipelineConfigurationError(
            "ANALYSIS_MODE=agents requires OPENAI_API_KEY. Fixture analysis does not."
        )

    from agents import Runner

    aspiration_input = json.dumps(
        {
            "task": "Build the aspirational style profile.",
            "evidence": _evidence_for(payload, "aspirational"),
        }
    )
    purchase_input = json.dumps(
        {
            "task": "Build the observed purchase style profile.",
            "evidence": [
                *_evidence_for(payload, "purchase"),
                *_evidence_for(payload, "survey"),
            ],
            "survey": payload.get("survey", []),
        }
    )
    aspiration_result, purchase_result = await asyncio.gather(
        Runner.run(
            create_aspiration_agent(
                settings.tagger_model, settings.tagger_reasoning_effort
            ),
            aspiration_input,
            run_config=run_config,
        ),
        Runner.run(
            create_purchase_signal_agent(
                settings.tagger_model, settings.tagger_reasoning_effort
            ),
            purchase_input,
            run_config=run_config,
        ),
    )
    aspiration = cast(StyleProfile, aspiration_result.final_output)
    behavior = cast(StyleProfile, purchase_result.final_output)
    if not isinstance(aspiration, StyleProfile) or not isinstance(behavior, StyleProfile):
        raise PipelineConfigurationError("Specialist agents did not return typed style profiles.")
    return aspiration, behavior


async def _synthesize_narrative(
    payload: dict[str, Any],
    aspiration: StyleProfile,
    behavior: StyleProfile,
    run_config: RunConfig,
) -> ReportNarrative:
    from agents import Runner

    scored_report = build_gap_report(payload, aspiration=aspiration, behavior=behavior)
    synthesis_input = json.dumps(
        {
            "task": "Write a grounded RealCart self-reflection narrative.",
            "persona": payload["persona"],
            "aspiration_profile": aspiration.model_dump(),
            "behavior_profile": behavior.model_dump(),
            "gap_score": scored_report.gap_score,
            "dimensions": [item.model_dump() for item in scored_report.dimensions],
            "allowed_evidence_ids": [item.id for item in scored_report.evidence],
        }
    )
    result = await Runner.run(
        create_report_manager_agent(
            settings.synthesis_model, settings.synthesis_reasoning_effort
        ),
        synthesis_input,
        run_config=run_config,
    )
    narrative = cast(ReportNarrative, result.final_output)
    if not isinstance(narrative, ReportNarrative):
        raise PipelineConfigurationError("Report manager did not return a typed narrative.")
    return narrative


def _agent_run_config(*, trace_id: str | None, group_id: str) -> RunConfig:
    from agents import RunConfig

    return RunConfig(
        tracing_disabled=not settings.openai_tracing_enabled,
        trace_include_sensitive_data=settings.trace_include_sensitive_data,
        workflow_name="RealCart GPT-5.6 analysis",
        trace_id=trace_id,
        group_id=group_id,
        trace_metadata={
            "specialist_model": settings.tagger_model,
            "synthesis_model": settings.synthesis_model,
        },
    )


async def run_pipeline(
    *,
    connector: SignalConnector | None = None,
    data_mode: str | None = None,
    analysis_mode: str | None = None,
) -> AnalysisRun:
    """Run the complete pipeline and return a typed, inspectable result."""

    selected_data_mode = data_mode or settings.data_mode
    selected_analysis_mode = analysis_mode or settings.analysis_mode
    payload = (connector or _connector_for(selected_data_mode)).load()
    stages = [
        AnalysisStage(
            name="fetch",
            detail=f"Loaded normalized evidence using {selected_data_mode} data.",
        )
    ]

    if selected_analysis_mode == "fixture":
        report = build_gap_report(payload)
        model_runtime = ModelRuntime(provider="fixture")
        stages.extend(
            [
                AnalysisStage(
                    name="specialist_analysis",
                    detail="Used deterministic synthetic specialist profiles for local testing.",
                ),
                AnalysisStage(
                    name="scoring",
                    detail="Calculated numeric gaps in application code.",
                ),
                AnalysisStage(
                    name="synthesis",
                    detail="Rendered the deterministic grounded fixture narrative.",
                ),
            ]
        )
    elif selected_analysis_mode == "agents":
        if not getenv("OPENAI_API_KEY"):
            raise PipelineConfigurationError(
                "ANALYSIS_MODE=agents requires OPENAI_API_KEY. Fixture analysis does not."
            )

        from agents import gen_trace_id, trace

        trace_id = gen_trace_id() if settings.openai_tracing_enabled else None
        group_id = f"realcart-{uuid4().hex}"
        run_config = _agent_run_config(trace_id=trace_id, group_id=group_id)
        try:
            with trace(
                "RealCart GPT-5.6 analysis",
                trace_id=trace_id,
                group_id=group_id,
                metadata={
                    "specialist_model": settings.tagger_model,
                    "synthesis_model": settings.synthesis_model,
                },
                disabled=not settings.openai_tracing_enabled,
            ):
                aspiration, behavior = await _run_specialist_agents(payload, run_config)
                stages.append(
                    AnalysisStage(
                        name="specialist_analysis",
                        detail=(
                            "Ran aspiration and purchase specialists concurrently with "
                            f"{settings.tagger_model}."
                        ),
                    )
                )
                narrative = await _synthesize_narrative(
                    payload, aspiration, behavior, run_config
                )
                report = build_gap_report(
                    payload,
                    aspiration=aspiration,
                    behavior=behavior,
                    narrative=narrative,
                )
        except PipelineConfigurationError:
            raise
        except Exception as error:
            raise PipelineExecutionError(_model_execution_error_message(error)) from error

        model_runtime = ModelRuntime(
            provider="openai",
            specialist_model=settings.tagger_model,
            specialist_reasoning_effort=settings.tagger_reasoning_effort,
            synthesis_model=settings.synthesis_model,
            synthesis_reasoning_effort=settings.synthesis_reasoning_effort,
            trace_id=trace_id,
        )
        stages.extend(
            [
                AnalysisStage(
                    name="scoring",
                    detail="Calculated numeric gaps in application code.",
                ),
                AnalysisStage(
                    name="synthesis",
                    detail=(
                        "Ran the report manager on typed profiles and precomputed scores with "
                        f"{settings.synthesis_model}."
                    ),
                ),
            ]
        )
    else:
        raise PipelineConfigurationError(
            f"Unsupported ANALYSIS_MODE: {selected_analysis_mode}"
        )

    return AnalysisRun(
        data_mode=selected_data_mode,
        analysis_mode=selected_analysis_mode,
        model_runtime=model_runtime,
        stages=stages,
        report=report,
    )
