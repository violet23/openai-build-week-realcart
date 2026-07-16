"""Connector protocol for fixture and future live implementations."""

from typing import Any, Protocol


class SignalConnector(Protocol):
    def load(self) -> dict[str, Any]:
        """Return normalized source data."""
        ...


class LiveConnectorNotConfigured(RuntimeError):
    """Raised when a live connector is used before its privacy gate is complete."""
