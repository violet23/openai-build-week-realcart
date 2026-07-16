"""FastAPI entry point for the fixture-first RealCart skeleton."""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from realcart_api.connectors import FixtureConnector
from realcart_api.schemas import (
    CandidateItem,
    DemoResponse,
    GapReport,
    SecondOpinionRequest,
    SecondOpinionResponse,
    SurveyQuestion,
)
from realcart_api.scoring import build_gap_report, build_second_opinion
from realcart_api.settings import settings

app = FastAPI(
    title="RealCart API",
    version="0.1.0",
    description="Evidence-led self-reflection without product recommendations.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _load_fixture() -> dict[str, Any]:
    if settings.data_mode != "fixture":
        raise HTTPException(
            status_code=501,
            detail="Live mode is not enabled; use DATA_MODE=fixture for this scaffold.",
        )
    return FixtureConnector().load()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "data_mode": settings.data_mode}


@app.get("/api/report", response_model=GapReport)
def report() -> GapReport:
    return build_gap_report(_load_fixture())


@app.get("/api/demo", response_model=DemoResponse)
def demo() -> DemoResponse:
    payload = _load_fixture()
    return DemoResponse(
        persona=payload["persona"],
        report=build_gap_report(payload),
        survey=[SurveyQuestion.model_validate(item) for item in payload["survey"]],
        candidate=CandidateItem.model_validate(payload["candidate"]),
    )


@app.post("/api/second-opinion", response_model=SecondOpinionResponse)
def second_opinion(candidate: SecondOpinionRequest) -> SecondOpinionResponse:
    return build_second_opinion(_load_fixture(), CandidateItem.model_validate(candidate))
