from collections.abc import Iterator
from typing import Any

import pytest

from realcart_api.connectors import FixtureConnector


@pytest.fixture
def fixture_payload() -> Iterator[dict[str, Any]]:
    yield FixtureConnector().load()
