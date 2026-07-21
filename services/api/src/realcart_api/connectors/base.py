"""Connector protocol and shared live-source errors."""

from typing import Any, Protocol


class SignalConnector(Protocol):
    def load(self) -> dict[str, Any]:
        """Return normalized source data."""
        ...


class LiveConnectorNotConfigured(RuntimeError):
    """Raised when a live connector lacks credentials or usable provider data."""
