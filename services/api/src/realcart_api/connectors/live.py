"""Combined live connector for Gmail purchase patterns and Pinterest saved signals."""

from __future__ import annotations

from typing import Any

from realcart_api.connectors.gmail import GmailConnector
from realcart_api.connectors.pinterest import PinterestConnector


class LiveConnector:
    def __init__(
        self,
        *,
        gmail: GmailConnector | None = None,
        pinterest: PinterestConnector | None = None,
    ) -> None:
        self.gmail = gmail or GmailConnector()
        self.pinterest = pinterest or PinterestConnector()

    def load(self) -> dict[str, Any]:
        gmail = self.gmail.load()
        pinterest = self.pinterest.load()
        return {
            "persona": {
                "id": "connected-user",
                "display_name": "Your RealCart",
                "description": "A private profile built from connected, user-authorized sources.",
            },
            "aspirational_items": pinterest["aspirational_items"],
            "purchase_items": gmail["purchase_items"],
            "evidence": [*pinterest["evidence"], *gmail["evidence"]],
            "survey": gmail["survey"],
            "portraits": [],
        }
