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
    assert payload["report"]["score_provenance"] == {
        "aspirational_item_count": 4,
        "purchase_item_count": 4,
        "kept_purchase_count": 3,
        "returned_item_count": 1,
        "profile_method": "fixture_item_average",
    }
    assert len(payload["survey"]) == 2
    assert payload["survey"][0]["merchant"] == "Everlane"
    assert payload["survey"][0]["price"] == 68
    assert payload["survey"][0]["image"]["image_url"].endswith("hoodie.svg")
    assert payload["survey"][0]["returned"] is False
    assert payload["survey"][0]["comment_prompt"]
    assert payload["survey"][1]["returned"] is True
    assert {prompt["key"] for prompt in payload["survey"][0]["prompts"]} == {
        "emotional_feedback",
        "usage_frequency",
        "purchase_motivation",
    }
    assert {prompt["key"] for prompt in payload["survey"][1]["prompts"]} == {
        "return_reason",
        "return_sentiment",
        "purchase_motivation",
    }
    assert len(payload["report"]["portraits"]) == 2
    assert {item["kind"] for item in payload["report"]["portraits"]} == {
        "style_world",
        "purchase_reality",
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
async def test_survey_answers_rerun_the_analysis() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/analyze",
            json={
                "answers": [
                    {
                        "item_id": "purchase-01",
                        "values": {
                            "emotional_feedback": "Love it",
                            "usage_frequency": "Often",
                            "purchase_motivation": "Needed it",
                        },
                        "notes": "It became a weekly staple.",
                    }
                ]
            },
        )

    assert response.status_code == 200
    assert response.json()["report"]["persona_name"] == "Demo: Maya"


@pytest.mark.asyncio
async def test_removed_second_opinion_route_is_not_available() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/second-opinion", json={})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_fixture_images_are_served() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/fixture-assets/hoodie.svg")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
