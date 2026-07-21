import base64
from pathlib import Path
from typing import Any

import httpx

from realcart_api.assets import AssetStore
from realcart_api.connectors.gmail import GmailConnector
from realcart_api.connectors.pinterest import PinterestConnector
from realcart_api.schemas import ImageAsset


def _encoded(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def test_gmail_connector_builds_image_backed_return_survey(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/messages"):
            return httpx.Response(200, json={"messages": [{"id": "message-1"}]})
        return httpx.Response(
            200,
            json={
                "id": "message-1",
                "internalDate": "1782777600000",
                "payload": {
                    "mimeType": "multipart/related",
                    "headers": [
                        {"name": "Subject", "value": "Your order #ABC-123 was returned"},
                        {"name": "From", "value": "Studio Shop <orders@shop.test>"},
                    ],
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {
                                "data": _encoded(
                                    b"Camel jacket. Your refund is confirmed. Total $189.00"
                                )
                            },
                        },
                        {
                            "mimeType": "image/png",
                            "body": {"data": _encoded(b"synthetic-png-fixture")},
                        },
                    ],
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    store = AssetStore(tmp_path, "http://test")

    payload = GmailConnector(
        access_token="gmail-token", store=store, client=client
    ).load()

    purchase = payload["purchase_items"][0]
    survey = payload["survey"][0]
    assert purchase["returned"] is True
    assert purchase["price"] == 189
    assert purchase["image"]["source"] == "gmail"
    assert purchase["_image_data_url"].startswith("data:image/png;base64,")
    assert survey["image"] == purchase["image"]
    assert {prompt["key"] for prompt in survey["prompts"]} == {
        "return_reason",
        "return_sentiment",
        "purchase_motivation",
    }


class _PinterestStore(AssetStore):
    def cache_remote_image(
        self,
        url: str,
        *,
        source: str,
        alt_text: str,
        client: httpx.Client | None = None,
    ) -> ImageAsset:
        del url, client
        return self.store_bytes(
            b"synthetic-pinterest-image",
            source="pinterest",
            alt_text=alt_text,
            mime_type="image/jpeg",
        )


def test_pinterest_sandbox_connector_normalizes_pin_images(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/boards"):
            return httpx.Response(
                200, json={"items": [{"id": "board-1", "name": "Quiet city life"}]}
            )
        if request.url.path.endswith("/boards/board-1/pins"):
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "id": "pin-1",
                            "title": "Warm tailored street scene",
                            "description": "Camel coat, stone street and soft morning light",
                            "media": {"images": {"1200x": {"url": "https://img.test/pin.jpg"}}},
                        }
                    ]
                },
            )
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    store = _PinterestStore(tmp_path, "http://test")

    payload = PinterestConnector(
        access_token="pinterest-token", store=store, client=client
    ).load()

    item: dict[str, Any] = payload["aspirational_items"][0]
    assert item["id"] == "pin-pin-1"
    assert item["board_name"] == "Quiet city life"
    assert item["image"]["source"] == "pinterest"
    assert item["_image_data_url"].startswith("data:image/jpeg;base64,")
    assert payload["evidence"][0]["kind"] == "aspirational"
