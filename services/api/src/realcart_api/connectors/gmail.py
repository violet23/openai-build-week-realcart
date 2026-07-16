"""Placeholder for a minimal, read-only Gmail receipt connector."""

from typing import Any

from realcart_api.connectors.base import LiveConnectorNotConfigured


class GmailConnector:
    def load(self) -> dict[str, Any]:
        raise LiveConnectorNotConfigured(
            "Gmail live mode is gated on OAuth, deletion, redaction, and consent tests."
        )
