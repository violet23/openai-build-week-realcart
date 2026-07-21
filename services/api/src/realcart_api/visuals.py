"""Generate the two visual summaries that accompany a RealCart report."""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Literal, cast

from openai import AsyncOpenAI

from realcart_api.assets import AssetStore, asset_store
from realcart_api.schemas import GapReport, GeneratedPortrait
from realcart_api.settings import settings


class PortraitGenerationError(RuntimeError):
    """Raised when a configured report portrait cannot be generated."""


def _portrait_prompt(report: GapReport, kind: Literal["style_world", "purchase_reality"]) -> str:
    dimensions = ", ".join(
        f"{item.label}: {getattr(item, 'aspiration' if kind == 'style_world' else 'behavior'):.2f}"
        for item in report.dimensions
    )
    themes = ", ".join(theme.name for theme in report.vision_themes[:5]) or "no repeated theme"
    subject = (
        "the saved-image Style World"
        if kind == "style_world"
        else "observed Purchase Reality"
    )
    return (
        "Create one editorial fashion-and-lifestyle self-portrait as a symbolic visual profile, "
        "not a portrait of a real identifiable person. Show a faceless full-body silhouette in an "
        "environment whose palette, materials, structure, texture, ornamentation, and polish "
        f"express {subject}. Style dimensions: {dimensions}. Repeated Style World themes: "
        f"{themes}. Use a refined magazine-collage aesthetic, soft natural depth, and a coherent "
        "single composition. Do not include text, numbers, product logos, brand marks, shopping "
        "interfaces, split screens, or a recommendation. The image is a reflective summary, not "
        "a claim about identity or psychology. Vertical 2:3 composition."
    )


async def _generate_one(
    client: AsyncOpenAI,
    report: GapReport,
    kind: Literal["style_world", "purchase_reality"],
    store: AssetStore,
) -> GeneratedPortrait:
    response = await client.images.generate(
        model=settings.image_model,
        prompt=_portrait_prompt(report, kind),
        n=1,
        quality="medium",
        size="1024x1536",
        output_format="webp",
        response_format="b64_json",
    )
    data = cast(Any, response).data
    encoded = data[0].b64_json if data else None
    if not isinstance(encoded, str) or not encoded:
        raise PortraitGenerationError("OpenAI returned no image data for a report portrait")
    image = store.store_bytes(
        base64.b64decode(encoded),
        source="generated",
        alt_text=(
            "Generated visual portrait of the Style World"
            if kind == "style_world"
            else "Generated visual portrait of Purchase Reality"
        ),
        mime_type="image/webp",
    )
    return GeneratedPortrait(
        kind=kind,
        title="Style World" if kind == "style_world" else "Purchase Reality",
        image=image,
        evidence_ids=[item.id for item in report.evidence],
        model=settings.image_model,
        generation_mode="openai",
    )


async def generate_portraits(
    report: GapReport, *, store: AssetStore | None = None
) -> list[GeneratedPortrait]:
    """Return fixture portraits or generate two evidence-derived visual summaries."""

    if settings.image_generation_mode == "fixture":
        return report.portraits
    if settings.image_generation_mode != "openai":
        raise PortraitGenerationError(
            "IMAGE_GENERATION_MODE must be either fixture or openai"
        )
    client = AsyncOpenAI()
    active_store = store or asset_store
    style_world, purchase_reality = await asyncio.gather(
        _generate_one(client, report, "style_world", active_store),
        _generate_one(client, report, "purchase_reality", active_store),
    )
    return [style_world, purchase_reality]
