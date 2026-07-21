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
from realcart_api.connectors import FixtureConnector, LiveConnector
from realcart_api.connectors.base import LiveConnectorNotConfigured, SignalConnector
from realcart_api.schemas import (
    AnalysisRun,
    AnalysisStage,
    ModelRuntime,
    ReportNarrative,
    StyleProfile,
    VisionProfile,
)
from realcart_api.scoring import build_gap_report
from realcart_api.settings import settings
from realcart_api.visuals import PortraitGenerationError, generate_portraits

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
            f"({settings.tagger_model}, {settings.synthesis_model}, {settings.image_model})."
        )
    if isinstance(error, BadRequestError):
        suffix = f" ({code})" if code else ""
        return (
            f"OpenAI rejected a configured model request{suffix}. Check model access, "
            "parameters, and the structured-output schema."
        )
    if isinstance(error, APIConnectionError):
        return "Could not connect to the OpenAI API. Check the network, proxy, and firewall."
    return (
        "OpenAI model execution failed "
        f"({type(error).__name__}). Inspect the agent trace for this run."
    )


def _connector_for(data_mode: str) -> SignalConnector:
    if data_mode == "fixture":
        return FixtureConnector()
    if data_mode == "live":
        return LiveConnector()
    raise PipelineConfigurationError(f"Unsupported DATA_MODE: {data_mode}")


def _evidence_for(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [item for item in payload["evidence"] if item["kind"] == kind]


def _items_without_fixture_scores(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            key: value
            for key, value in item.items()
            if key not in {"dimensions", "_image_data_url"}
        }
        for item in items
    ]


def _multimodal_input(
    *, task: str, evidence: list[dict[str, Any]], items: list[dict[str, Any]], extra: dict[str, Any]
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": json.dumps(
                {
                    "task": task,
                    "evidence": evidence,
                    "items": _items_without_fixture_scores(items),
                    **extra,
                }
            ),
        }
    ]
    for item in items:
        image_data_url = item.get("_image_data_url")
        if not isinstance(image_data_url, str):
            continue
        content.extend(
            [
                {
                    "type": "input_text",
                    "text": f"Image evidence for item {item.get('id', 'unknown')}",
                },
                {
                    "type": "input_image",
                    "image_url": image_data_url,
                    "detail": "high",
                },
            ]
        )
    return [{"role": "user", "content": content}]


async def _run_specialist_agents(
    payload: dict[str, Any], run_config: RunConfig
) -> tuple[VisionProfile, StyleProfile]:
    if not getenv("OPENAI_API_KEY"):
        raise PipelineConfigurationError(
            "ANALYSIS_MODE=agents requires OPENAI_API_KEY. Fixture analysis does not."
        )

    from agents import Runner

    aspiration_input = _multimodal_input(
        task="Build repeated saved-image style signals and their board-level themes.",
        evidence=_evidence_for(payload, "aspirational"),
        items=payload["aspirational_items"],
        extra={},
    )
    purchase_input = _multimodal_input(
        task="Build purchase patterns from observed shopping behavior and context.",
        evidence=[
            *_evidence_for(payload, "purchase"),
            *_evidence_for(payload, "survey"),
        ],
        items=payload["purchase_items"],
        extra={
            "survey": payload.get("survey", []),
            "survey_answers": payload.get("survey_answers", []),
        },
    )
    aspiration_result, purchase_result = await asyncio.gather(
        Runner.run(
            create_aspiration_agent(
                settings.tagger_model, settings.tagger_reasoning_effort
            ),
            cast(Any, aspiration_input),
            run_config=run_config,
        ),
        Runner.run(
            create_purchase_signal_agent(
                settings.tagger_model, settings.tagger_reasoning_effort
            ),
            cast(Any, purchase_input),
            run_config=run_config,
        ),
    )
    aspiration = cast(VisionProfile, aspiration_result.final_output)
    behavior = cast(StyleProfile, purchase_result.final_output)
    if not isinstance(aspiration, VisionProfile) or not isinstance(behavior, StyleProfile):
        raise PipelineConfigurationError("Specialist agents did not return typed style profiles.")
    return aspiration, behavior


async def _synthesize_narrative(
    payload: dict[str, Any],
    aspiration: VisionProfile,
    behavior: StyleProfile,
    run_config: RunConfig,
) -> ReportNarrative:
    from agents import Runner

    scored_report = build_gap_report(
        payload,
        aspiration=aspiration,
        behavior=behavior,
        vision_themes=aspiration.themes,
    )
    synthesis_input = json.dumps(
        {
            "task": "Write a grounded RealCart self-reflection narrative.",
            "persona": payload["persona"],
            "aspiration_profile": aspiration.model_dump(),
            "vision_themes": [theme.model_dump() for theme in aspiration.themes],
            "behavior_profile": behavior.model_dump(),
            "purchase_records": [
                {
                    key: item.get(key)
                    for key in (
                        "id",
                        "label",
                        "merchant",
                        "price",
                        "currency",
                        "returned",
                        "category",
                        "style_tags",
                    )
                }
                for item in payload["purchase_items"]
            ],
            "survey_answers": payload.get("survey_answers", []),
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
    try:
        payload = await asyncio.to_thread(
            (connector or _connector_for(selected_data_mode)).load
        )
    except LiveConnectorNotConfigured as error:
        raise PipelineConfigurationError(str(error)) from error
    stages = [
        AnalysisStage(
            name="fetch",
            detail=f"Loaded normalized evidence using {selected_data_mode} data.",
        )
    ]

    if selected_analysis_mode == "fixture":
        report = build_gap_report(payload)
        if settings.image_generation_mode == "openai" and not getenv("OPENAI_API_KEY"):
            raise PipelineConfigurationError(
                "IMAGE_GENERATION_MODE=openai requires OPENAI_API_KEY."
            )
        try:
            report.portraits = await generate_portraits(report)
        except PortraitGenerationError as error:
            raise PipelineExecutionError(str(error)) from error
        except Exception as error:
            raise PipelineExecutionError(_model_execution_error_message(error)) from error
        model_runtime = ModelRuntime(
            provider="fixture",
            image_model=(
                settings.image_model
                if settings.image_generation_mode == "openai"
                else "fixture"
            ),
        )
        stages.extend(
            [
                AnalysisStage(
                    name="specialist_analysis",
                    detail=(
                        "Aggregated confidence-weighted saved-image and kept-purchase signals "
                        "into deterministic profiles."
                    ),
                ),
                AnalysisStage(
                    name="scoring",
                    detail="Calculated numeric signal differences in application code.",
                ),
                AnalysisStage(
                    name="synthesis",
                    detail="Rendered the deterministic grounded fixture narrative.",
                ),
                AnalysisStage(
                    name="visual_generation",
                    detail=(
                        "Generated two evidence-derived portraits with "
                        f"{settings.image_model}."
                        if settings.image_generation_mode == "openai"
                        else "Loaded two synthetic visual fixtures for the report."
                    ),
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
                            "Ran Saved Style Signals and Purchase Patterns specialists "
                            f"concurrently with {settings.tagger_model}."
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
                    vision_themes=aspiration.themes,
                )
                report.portraits = await generate_portraits(report)
        except PipelineConfigurationError:
            raise
        except PortraitGenerationError as error:
            raise PipelineExecutionError(str(error)) from error
        except Exception as error:
            raise PipelineExecutionError(_model_execution_error_message(error)) from error

        model_runtime = ModelRuntime(
            provider="openai",
            specialist_model=settings.tagger_model,
            specialist_reasoning_effort=settings.tagger_reasoning_effort,
            synthesis_model=settings.synthesis_model,
            synthesis_reasoning_effort=settings.synthesis_reasoning_effort,
            image_model=(
                settings.image_model
                if settings.image_generation_mode == "openai"
                else "fixture"
            ),
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
                AnalysisStage(
                    name="visual_generation",
                    detail=(
                        "Generated two evidence-derived portraits with "
                        f"{settings.image_model}."
                        if settings.image_generation_mode == "openai"
                        else "Loaded fixture portraits; set IMAGE_GENERATION_MODE=openai "
                        "to generate new report visuals."
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
