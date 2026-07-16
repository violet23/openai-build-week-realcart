"""Placeholder for a Pinterest sandbox/live connector."""

from typing import Any

from realcart_api.connectors.base import LiveConnectorNotConfigured


class PinterestConnector:
    def load(self) -> dict[str, Any]:
        raise LiveConnectorNotConfigured(
            "Pinterest live mode is gated on sandbox, OAuth, and consent tests."
        )
