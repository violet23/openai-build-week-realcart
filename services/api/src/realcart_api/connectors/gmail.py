"""Read-only Gmail connector for order, receipt, return, and product-image evidence."""

from __future__ import annotations

import base64
import re
from datetime import UTC, datetime
from email.utils import parseaddr
from html.parser import HTMLParser
from typing import Any

import httpx

from realcart_api.assets import AssetStore, ImageAssetError, asset_store
from realcart_api.connectors.base import LiveConnectorNotConfigured
from realcart_api.connectors.oauth import oauth_store
from realcart_api.schemas import ImageAsset
from realcart_api.settings import settings

_GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"
_PRICE_PATTERN = re.compile(r"(?:US\s*)?\$\s*([0-9][0-9,]*(?:\.\d{2})?)", re.I)
_ORDER_PATTERN = re.compile(
    r"(?:order(?:\s+(?:number|no\.?))?|order\s*#)\s*[:#-]?\s*([A-Z0-9-]{4,})",
    re.I,
)
_RETURN_WORDS = ("return", "returned", "refund", "refunded")
_IGNORED_IMAGE_WORDS = (
    "avatar",
    "badge",
    "banner",
    "facebook",
    "icon",
    "instagram",
    "logo",
    "pixel",
    "spacer",
    "tracking",
    "twitter",
)


class _HTMLReceiptParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.images: list[tuple[str, str]] = []

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped:
            self.text_parts.append(stripped)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        src = values.get("src", "").strip()
        alt = values.get("alt", "").strip()
        if src:
            self.images.append((src, alt))


def _decode_base64url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _walk_parts(part: dict[str, Any]) -> list[dict[str, Any]]:
    parts = [part]
    for child in part.get("parts", []):
        if isinstance(child, dict):
            parts.extend(_walk_parts(child))
    return parts


def _header_map(payload: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for header in payload.get("headers", []):
        if isinstance(header, dict):
            name = header.get("name")
            value = header.get("value")
            if isinstance(name, str) and isinstance(value, str):
                result[name.lower()] = value
    return result


def _likely_product_image(url: str, alt: str) -> bool:
    normalized = f"{url} {alt}".lower()
    if not url.startswith("https://"):
        return False
    if any(word in normalized for word in _IGNORED_IMAGE_WORDS):
        return False
    return bool(alt.strip()) and len(alt.strip()) >= 3


def _survey_prompts(item_id: str, returned: bool) -> list[dict[str, Any]]:
    if returned:
        return [
            {
                "id": f"{item_id}-return-reason",
                "key": "return_reason",
                "question": "Why did you return it?",
                "options": [
                    "Fit or comfort",
                    "Quality",
                    "Looked different",
                    "Price or value",
                    "Changed my mind",
                ],
            },
            {
                "id": f"{item_id}-return-sentiment",
                "key": "return_sentiment",
                "question": "How did returning it feel?",
                "options": ["Relieved", "Neutral", "Still wanted it", "Regret returning it"],
            },
            {
                "id": f"{item_id}-motivation",
                "key": "purchase_motivation",
                "question": "What drove the purchase?",
                "options": [
                    "Needed it",
                    "Matched my taste",
                    "On sale",
                    "Impulse or influence",
                ],
            },
        ]
    return [
        {
            "id": f"{item_id}-feeling",
            "key": "emotional_feedback",
            "question": "How do you feel about it now?",
            "options": ["Love it", "Neutral", "Regret it"],
        },
        {
            "id": f"{item_id}-frequency",
            "key": "usage_frequency",
            "question": "How often do you wear or use it?",
            "options": ["Often", "Sometimes", "Rarely", "Never"],
        },
        {
            "id": f"{item_id}-motivation",
            "key": "purchase_motivation",
            "question": "What drove the purchase?",
            "options": [
                "Needed it",
                "Matched my taste",
                "On sale",
                "Impulse or influence",
            ],
        },
    ]


class GmailConnector:
    def __init__(
        self,
        *,
        access_token: str | None = None,
        store: AssetStore | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.access_token = access_token or oauth_store.access_token("gmail")
        self.store = store or asset_store
        self.client = client

    def load(self) -> dict[str, Any]:
        if not self.access_token:
            raise LiveConnectorNotConfigured(
                "Connect Gmail or set GMAIL_ACCESS_TOKEN before using DATA_MODE=live."
            )
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=20, follow_redirects=True)
        try:
            message_ids = self._list_message_ids(client)
            records = [
                record
                for message_id in message_ids
                if (record := self._load_message(client, message_id)) is not None
            ]
        finally:
            if owns_client:
                client.close()
        records = self._merge_return_records(records)
        return {
            "purchase_items": [record["purchase"] for record in records],
            "survey": [record["survey"] for record in records],
            "evidence": [record["evidence"] for record in records],
        }

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def _list_message_ids(self, client: httpx.Client) -> list[str]:
        response = client.get(
            f"{_GMAIL_API}/messages",
            headers=self._headers(),
            params={
                "q": settings.gmail_purchase_query,
                "maxResults": settings.gmail_max_messages,
            },
        )
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise LiveConnectorNotConfigured("Gmail message search failed") from error
        if not isinstance(payload, dict):
            return []
        return [
            item["id"]
            for item in payload.get("messages", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]

    def _load_message(
        self, client: httpx.Client, message_id: str
    ) -> dict[str, Any] | None:
        response = client.get(
            f"{_GMAIL_API}/messages/{message_id}",
            headers=self._headers(),
            params={"format": "full"},
        )
        try:
            response.raise_for_status()
            message = response.json()
        except (httpx.HTTPError, ValueError):
            return None
        if not isinstance(message, dict) or not isinstance(message.get("payload"), dict):
            return None

        payload: dict[str, Any] = message["payload"]
        headers = _header_map(payload)
        subject = headers.get("subject", "Order receipt").strip()
        merchant = parseaddr(headers.get("from", ""))[0] or parseaddr(
            headers.get("from", "")
        )[1].split("@", 1)[0]
        text_parts: list[str] = []
        html_parsers: list[_HTMLReceiptParser] = []
        inline_image: ImageAsset | None = None
        inline_candidates: list[tuple[bytes, str, str]] = []

        for part in _walk_parts(payload):
            mime_type = str(part.get("mimeType", "")).lower()
            body = part.get("body", {})
            if not isinstance(body, dict):
                continue
            part_data = self._part_data(client, message_id, body)
            if part_data is None:
                continue
            if mime_type in {"text/plain", "text/html"}:
                decoded = part_data.decode("utf-8", errors="replace")
                if mime_type == "text/html":
                    parser = _HTMLReceiptParser()
                    parser.feed(decoded)
                    html_parsers.append(parser)
                    text_parts.extend(parser.text_parts)
                else:
                    text_parts.append(decoded)
            elif mime_type in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
                filename = str(part.get("filename") or "")
                if not any(word in filename.lower() for word in _IGNORED_IMAGE_WORDS):
                    inline_candidates.append((part_data, mime_type, filename or subject))

        for image_data, mime_type, alt_text in sorted(
            inline_candidates, key=lambda item: len(item[0]), reverse=True
        ):
            try:
                inline_image = self.store.store_bytes(
                    image_data,
                    source="gmail",
                    alt_text=alt_text,
                    mime_type=mime_type,
                )
                break
            except ImageAssetError:
                continue

        receipt_text = " ".join(text_parts)
        external_alt = ""
        if inline_image is None:
            for parser in html_parsers:
                for image_url, alt in parser.images:
                    if not _likely_product_image(image_url, alt):
                        continue
                    try:
                        inline_image = self.store.cache_remote_image(
                            image_url,
                            source="gmail",
                            alt_text=alt or subject,
                            client=client,
                        )
                    except ImageAssetError:
                        continue
                    external_alt = alt
                    break
                if inline_image is not None:
                    break

        combined_text = f"{subject} {receipt_text}"
        price_matches = _PRICE_PATTERN.findall(combined_text)
        price = float(price_matches[-1].replace(",", "")) if price_matches else None
        returned = any(word in combined_text.lower() for word in _RETURN_WORDS)
        label = external_alt.strip() or subject
        label = re.sub(
            r"^(re:|fwd:|your\s+|order\s+confirmed:?\s*|receipt:?\s*)",
            "",
            label,
            flags=re.I,
        ).strip() or "Imported order item"
        order_match = _ORDER_PATTERN.search(combined_text)
        order_key = order_match.group(1).lower() if order_match else message_id
        item_id = f"gmail-{message_id}"
        purchased_at = datetime.fromtimestamp(
            int(message.get("internalDate", "0")) / 1000,
            tz=UTC,
        ).date().isoformat()
        image_payload = inline_image.model_dump() if inline_image is not None else None
        purchase: dict[str, Any] = {
            "id": item_id,
            "source": "gmail",
            "label": label,
            "merchant": merchant or "Unknown merchant",
            "price": price,
            "currency": "USD",
            "purchased_at": purchased_at,
            "returned": returned,
            "confidence": 0.65,
            "receipt_excerpt": receipt_text[:4000],
            "image": image_payload,
        }
        if inline_image is not None:
            purchase["_image_data_url"] = self.store.data_url_for(inline_image)
        survey = {
            "id": f"check-in-{item_id}",
            "item_id": item_id,
            "item_name": label,
            "merchant": merchant or "Unknown merchant",
            "price": price,
            "currency": "USD",
            "purchased_at": purchased_at,
            "returned": returned,
            "image": image_payload,
            "comment_prompt": (
                "Anything else you want us to understand about this return?"
                if returned
                else "Anything else about how this item fits into your life?"
            ),
            "prompts": _survey_prompts(item_id, returned),
        }
        return {
            "order_key": order_key,
            "purchase": purchase,
            "survey": survey,
            "evidence": {
                "id": item_id,
                "source": "gmail",
                "label": label,
                "kind": "purchase",
            },
        }

    def _part_data(
        self, client: httpx.Client, message_id: str, body: dict[str, Any]
    ) -> bytes | None:
        data = body.get("data")
        if isinstance(data, str) and data:
            try:
                return _decode_base64url(data)
            except (ValueError, TypeError):
                return None
        attachment_id = body.get("attachmentId")
        if not isinstance(attachment_id, str) or not attachment_id:
            return None
        response = client.get(
            f"{_GMAIL_API}/messages/{message_id}/attachments/{attachment_id}",
            headers=self._headers(),
        )
        try:
            response.raise_for_status()
            payload = response.json()
            attachment_data = payload.get("data")
            return (
                _decode_base64url(attachment_data)
                if isinstance(attachment_data, str)
                else None
            )
        except (httpx.HTTPError, ValueError, TypeError):
            return None

    def _merge_return_records(
        self, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for record in records:
            key = str(record["order_key"])
            existing = merged.get(key)
            if existing is None:
                merged[key] = record
                continue
            if bool(record["purchase"].get("returned")):
                existing["purchase"]["returned"] = True
                existing["survey"]["returned"] = True
                item_id = str(existing["purchase"]["id"])
                existing["survey"]["prompts"] = _survey_prompts(item_id, True)
                existing["survey"]["comment_prompt"] = (
                    "Anything else you want us to understand about this return?"
                )
        return list(merged.values())
