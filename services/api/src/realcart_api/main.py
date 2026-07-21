"""FastAPI entry point for RealCart's image-backed reflection pipeline."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Literal, NoReturn

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from realcart_api.assets import asset_store
from realcart_api.connectors import FixtureConnector, LiveConnector
from realcart_api.connectors.base import LiveConnectorNotConfigured
from realcart_api.connectors.oauth import (
    OAuthConfigurationError,
    authorization_url,
    exchange_code,
    oauth_store,
)
from realcart_api.pipeline import (
    PipelineConfigurationError,
    PipelineExecutionError,
    run_pipeline,
)
from realcart_api.schemas import (
    AnalysisRequest,
    AnalysisRun,
    ConnectionOverview,
    DemoResponse,
    GapReport,
    PurchaseSurveyItem,
    SourceConnection,
)
from realcart_api.settings import settings

app = FastAPI(
    title="RealCart API",
    version="0.2.0",
    description="Image-backed, evidence-led shopping-pattern reflection.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_FIXTURE_IMAGES = _REPO_ROOT / "fixtures" / "demo" / "images"


class _PayloadConnector:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def load(self) -> dict[str, Any]:
        return self.payload


def _connector() -> FixtureConnector | LiveConnector:
    if settings.data_mode == "fixture":
        return FixtureConnector()
    if settings.data_mode == "live":
        return LiveConnector()
    raise PipelineConfigurationError(f"Unsupported DATA_MODE: {settings.data_mode}")


async def _load_payload() -> dict[str, Any]:
    return await asyncio.to_thread(_connector().load)


def _raise_api_error(error: Exception) -> NoReturn:
    if isinstance(error, (PipelineConfigurationError, LiveConnectorNotConfigured)):
        raise HTTPException(status_code=503, detail=str(error)) from error
    if isinstance(error, PipelineExecutionError):
        raise HTTPException(status_code=502, detail=str(error)) from error
    raise error


def _append_survey_answers(
    payload: dict[str, Any], request: AnalysisRequest
) -> None:
    serialized = [answer.model_dump() for answer in request.answers]
    payload["survey_answers"] = serialized
    known_ids = {str(item.get("id")) for item in payload["evidence"]}
    for answer in request.answers:
        evidence_id = f"survey-{answer.item_id}"
        if evidence_id in known_ids:
            continue
        values = ", ".join(answer.values.values())
        payload["evidence"].append(
            {
                "id": evidence_id,
                "source": "user_survey",
                "label": f"Follow-up for {answer.item_id}: {values or 'comment only'}",
                "kind": "survey",
            }
        )


async def _demo_response(request: AnalysisRequest | None = None) -> DemoResponse:
    payload = await _load_payload()
    if request is not None:
        _append_survey_answers(payload, request)
    result = await run_pipeline(
        connector=_PayloadConnector(payload),
        data_mode=settings.data_mode,
        analysis_mode=settings.analysis_mode,
    )
    return DemoResponse(
        persona=payload["persona"],
        report=result.report,
        survey=[PurchaseSurveyItem.model_validate(item) for item in payload["survey"]],
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "data_mode": settings.data_mode}


@app.get("/api/connections", response_model=ConnectionOverview)
def connections() -> ConnectionOverview:
    api_base = settings.api_public_base_url
    return ConnectionOverview(
        data_mode=settings.data_mode,
        sources=[
            SourceConnection(
                source="gmail",
                configured=bool(settings.google_client_id and settings.google_client_secret),
                connected=oauth_store.connected("gmail"),
                environment="gmail",
                connect_url=f"{api_base}/api/auth/gmail/start",
            ),
            SourceConnection(
                source="pinterest",
                configured=bool(
                    settings.pinterest_client_id and settings.pinterest_client_secret
                ),
                connected=oauth_store.connected("pinterest"),
                environment="sandbox",
                connect_url=f"{api_base}/api/auth/pinterest/start",
            ),
        ],
    )


@app.get("/api/auth/{provider}/start")
def oauth_start(provider: Literal["gmail", "pinterest"]) -> RedirectResponse:
    try:
        return RedirectResponse(authorization_url(provider), status_code=302)
    except OAuthConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/auth/{provider}/callback")
async def oauth_callback(
    provider: Literal["gmail", "pinterest"], code: str, state: str
) -> RedirectResponse:
    try:
        await exchange_code(provider, code=code, state=state)
    except OAuthConfigurationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return RedirectResponse(
        f"{settings.web_public_base_url.rstrip('/')}?connected={provider}",
        status_code=302,
    )


@app.get("/api/assets/{asset_id}")
def asset(asset_id: str) -> FileResponse:
    path = asset_store.path_for(asset_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Image asset not found")
    return FileResponse(path, media_type=asset_store.mime_type_for(path))


@app.get("/api/fixture-assets/{name}")
def fixture_asset(name: str) -> FileResponse:
    if not name.endswith(".svg") or Path(name).name != name:
        raise HTTPException(status_code=404, detail="Fixture image not found")
    path = _FIXTURE_IMAGES / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fixture image not found")
    return FileResponse(path, media_type="image/svg+xml")


@app.get("/api/run", response_model=AnalysisRun)
async def analysis_run() -> AnalysisRun:
    try:
        return await run_pipeline()
    except Exception as error:
        _raise_api_error(error)


@app.get("/api/report", response_model=GapReport)
async def report() -> GapReport:
    return (await analysis_run()).report


@app.get("/api/demo", response_model=DemoResponse)
async def demo() -> DemoResponse:
    try:
        return await _demo_response()
    except Exception as error:
        _raise_api_error(error)


@app.post("/api/analyze", response_model=DemoResponse)
async def analyze(request: AnalysisRequest) -> DemoResponse:
    try:
        return await _demo_response(request)
    except Exception as error:
        _raise_api_error(error)
