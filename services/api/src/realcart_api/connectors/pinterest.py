"""Pinterest Sandbox connector for image-backed saved style signals."""

from __future__ import annotations

from typing import Any

import httpx

from realcart_api.assets import AssetStore, ImageAssetError, asset_store
from realcart_api.connectors.base import LiveConnectorNotConfigured
from realcart_api.connectors.oauth import oauth_store
from realcart_api.settings import settings


def _image_candidates(value: object) -> list[str]:
    if isinstance(value, dict):
        direct = [
            item
            for key, item in value.items()
            if key.lower() in {"url", "image_url", "cover_image_url"}
            and isinstance(item, str)
            and item.startswith("https://")
        ]
        nested: list[str] = []
        for child in value.values():
            nested.extend(_image_candidates(child))
        return [*direct, *nested]
    if isinstance(value, list):
        result: list[str] = []
        for child in value:
            result.extend(_image_candidates(child))
        return result
    return []


class PinterestConnector:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        store: AssetStore | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.access_token = access_token or oauth_store.access_token("pinterest")
        self.store = store or asset_store
        self.client = client

    def load(self) -> dict[str, Any]:
        if not self.access_token:
            raise LiveConnectorNotConfigured(
                "Connect Pinterest Sandbox or set PINTEREST_ACCESS_TOKEN before live mode."
            )
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=20, follow_redirects=True)
        try:
            boards = self._get_pages(client, "/boards")
            items: list[dict[str, Any]] = []
            evidence: list[dict[str, str]] = []
            for board in boards:
                board_id = board.get("id")
                if not isinstance(board_id, str):
                    continue
                board_name = str(board.get("name") or "Pinterest board")
                remaining = settings.pinterest_max_pins - len(items)
                for pin in self._get_pages(
                    client, f"/boards/{board_id}/pins", limit=remaining
                ):
                    if len(items) >= settings.pinterest_max_pins:
                        break
                    normalized = self._normalize_pin(client, pin, board_name)
                    if normalized is None:
                        continue
                    items.append(normalized)
                    evidence.append(
                        {
                            "id": str(normalized["id"]),
                            "source": "pinterest",
                            "label": str(normalized["label"]),
                            "kind": "aspirational",
                        }
                    )
                if len(items) >= settings.pinterest_max_pins:
                    break
        finally:
            if owns_client:
                client.close()
        if not items:
            raise LiveConnectorNotConfigured(
                "Pinterest Sandbox returned no readable image Pins. Add Pins to a sandbox board."
            )
        return {"aspirational_items": items, "evidence": evidence}

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def _get_pages(
        self, client: httpx.Client, path: str, *, limit: int | None = None
    ) -> list[dict[str, Any]]:
        bookmark: str | None = None
        results: list[dict[str, Any]] = []
        for _page in range(10):
            params: dict[str, str | int] = {"page_size": 100}
            if bookmark:
                params["bookmark"] = bookmark
            response = client.get(
                f"{settings.pinterest_api_base_url}{path}",
                headers=self._headers(),
                params=params,
            )
            try:
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as error:
                raise LiveConnectorNotConfigured(
                    f"Pinterest Sandbox request failed for {path}"
                ) from error
            if not isinstance(payload, dict):
                break
            results.extend(
                item for item in payload.get("items", []) if isinstance(item, dict)
            )
            if limit is not None and len(results) >= limit:
                break
            next_bookmark = payload.get("bookmark")
            if not isinstance(next_bookmark, str) or not next_bookmark:
                break
            bookmark = next_bookmark
        return results if limit is None else results[:limit]

    def _normalize_pin(
        self, client: httpx.Client, pin: dict[str, Any], board_name: str
    ) -> dict[str, Any] | None:
        pin_id = pin.get("id")
        if not isinstance(pin_id, str):
            return None
        title = str(pin.get("title") or pin.get("description") or "Pinterest image")
        image_urls = _image_candidates(pin.get("media", {}))
        if not image_urls:
            image_urls = _image_candidates(pin.get("media_source", {}))
        image = None
        for image_url in image_urls:
            try:
                image = self.store.cache_remote_image(
                    image_url,
                    source="pinterest",
                    alt_text=title,
                    client=client,
                )
                break
            except ImageAssetError:
                continue
        if image is None:
            return None
        return {
            "id": f"pin-{pin_id}",
            "source": "pinterest",
            "label": title,
            "board_name": board_name,
            "intent_type": "mixed",
            "literal_content": [title],
            "description": str(pin.get("description") or ""),
            "themes": [],
            "visual_evidence": [],
            "confidence": 0.8,
            "image": image.model_dump(),
            "_image_data_url": self.store.data_url_for(image),
        }
