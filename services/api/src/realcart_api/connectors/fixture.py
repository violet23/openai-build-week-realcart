"""Synthetic fixture connector used by local development, CI, and judges."""

import json
from pathlib import Path
from typing import Any


class FixtureConnector:
    def __init__(self, fixture_path: Path | None = None) -> None:
        repository_root = Path(__file__).resolve().parents[5]
        self.fixture_path = fixture_path or repository_root / "fixtures/demo/persona.json"

    def load(self) -> dict[str, Any]:
        with self.fixture_path.open(encoding="utf-8") as fixture_file:
            payload: dict[str, Any] = json.load(fixture_file)
        return payload
