import base64
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import realcart_api.visuals as visuals
from realcart_api.assets import AssetStore
from realcart_api.scoring import build_gap_report


@pytest.mark.asyncio
async def test_openai_portraits_are_stored_as_two_generated_assets(
    fixture_payload: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    class FakeImages:
        async def generate(self, **kwargs: Any) -> Any:
            calls.append(str(kwargs["prompt"]))
            return SimpleNamespace(
                data=[
                    SimpleNamespace(
                        b64_json=base64.b64encode(b"synthetic-webp").decode("ascii")
                    )
                ]
            )

    class FakeClient:
        images = FakeImages()

    monkeypatch.setattr(
        visuals,
        "settings",
        SimpleNamespace(image_generation_mode="openai", image_model="gpt-image-2"),
    )
    monkeypatch.setattr(visuals, "AsyncOpenAI", FakeClient)
    report = build_gap_report(fixture_payload)

    portraits = await visuals.generate_portraits(
        report, store=AssetStore(tmp_path, "http://test")
    )

    assert [portrait.kind for portrait in portraits] == [
        "style_world",
        "purchase_reality",
    ]
    assert all(portrait.image.source == "generated" for portrait in portraits)
    assert all(
        portrait.image.image_url.startswith("http://test/api/assets/")
        for portrait in portraits
    )
    assert len(calls) == 2
