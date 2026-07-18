import pytest
from httpx import ASGITransport, AsyncClient

from realcart_api.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "data_mode": "fixture"}


@pytest.mark.asyncio
async def test_demo_vertical_slice() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/demo")

    assert response.status_code == 200
    payload = response.json()
    assert payload["persona"]["display_name"] == "Demo: Maya"
    assert payload["report"]["gap_score"] > 0
    assert len(payload["survey"]) == 2
    assert payload["survey"][0]["merchant"] == "Everlane"
    assert payload["survey"][0]["price"] == 68
    assert payload["survey"][0]["returned"] is False
    assert payload["survey"][1]["returned"] is True
    assert {prompt["key"] for prompt in payload["survey"][0]["prompts"]} == {
        "emotional_feedback",
        "usage_frequency",
        "purchase_motivation",
    }


@pytest.mark.asyncio
async def test_pipeline_run() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_mode"] == "fixture"
    assert payload["analysis_mode"] == "fixture"
    assert payload["model_runtime"]["provider"] == "fixture"
    assert payload["stages"][0]["name"] == "fetch"


@pytest.mark.asyncio
async def test_second_opinion() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        demo = (await client.get("/api/demo")).json()
        response = await client.post("/api/second-opinion", json=demo["candidate"])

    assert response.status_code == 200
    assert response.json()["candidate_name"] == demo["candidate"]["name"]
