"""Backend-first orchestration for fetching, analysis, scoring, and synthesis."""

import asyncio
import json
from os import getenv
from typing import Any, cast

from realcart_api.agents.aspiration import create_aspiration_agent
from realcart_api.agents.purchase_signal import create_purchase_signal_agent
from realcart_api.agents.report_manager import create_report_manager_agent
from realcart_api.connectors import FixtureConnector
from realcart_api.connectors.base import SignalConnector
from realcart_api.schemas import AnalysisRun, AnalysisStage, ReportNarrative, StyleProfile
from realcart_api.scoring import build_gap_report
from realcart_api.settings import settings


class PipelineConfigurationError(RuntimeError):
    """Raised when a requested pipeline mode cannot run safely."""


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


async def _run_specialist_agents(payload: dict[str, Any]) -> tuple[StyleProfile, StyleProfile]:
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
        Runner.run(create_aspiration_agent(settings.tagger_model), aspiration_input),
        Runner.run(create_purchase_signal_agent(settings.tagger_model), purchase_input),
    )
    aspiration = cast(StyleProfile, aspiration_result.final_output)
    behavior = cast(StyleProfile, purchase_result.final_output)
    if not isinstance(aspiration, StyleProfile) or not isinstance(behavior, StyleProfile):
        raise PipelineConfigurationError("Specialist agents did not return typed style profiles.")
    return aspiration, behavior


async def _synthesize_narrative(
    payload: dict[str, Any], aspiration: StyleProfile, behavior: StyleProfile
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
        create_report_manager_agent(settings.synthesis_model), synthesis_input
    )
    narrative = cast(ReportNarrative, result.final_output)
    if not isinstance(narrative, ReportNarrative):
        raise PipelineConfigurationError("Report manager did not return a typed narrative.")
    return narrative


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
        aspiration, behavior = await _run_specialist_agents(payload)
        stages.append(
            AnalysisStage(
                name="specialist_analysis",
                detail="Ran aspiration and purchase specialists concurrently.",
            )
        )
        narrative = await _synthesize_narrative(payload, aspiration, behavior)
        report = build_gap_report(
            payload,
            aspiration=aspiration,
            behavior=behavior,
            narrative=narrative,
        )
        stages.extend(
            [
                AnalysisStage(
                    name="scoring",
                    detail="Calculated numeric gaps in application code.",
                ),
                AnalysisStage(
                    name="synthesis",
                    detail="Ran the report manager on typed profiles and precomputed scores.",
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
        stages=stages,
        report=report,
    )
