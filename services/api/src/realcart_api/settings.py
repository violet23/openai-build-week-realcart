"""Environment-backed runtime settings."""

from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from typing import Literal, cast

ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh", "max"]
_REASONING_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max"}


def _env(name: str, default: str) -> str:
    return getenv(name, default)


def _env_bool(name: str, default: bool) -> bool:
    value = getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


def _env_reasoning_effort(name: str, default: ReasoningEffort) -> ReasoningEffort:
    value = getenv(name, default).strip().lower()
    if value not in _REASONING_EFFORTS:
        choices = ", ".join(sorted(_REASONING_EFFORTS))
        raise ValueError(f"{name} must be one of: {choices}")
    return cast(ReasoningEffort, value)


@dataclass(frozen=True)
class Settings:
    data_mode: str = field(default_factory=lambda: _env("DATA_MODE", "fixture"))
    analysis_mode: str = field(default_factory=lambda: _env("ANALYSIS_MODE", "fixture"))
    tagger_model: str = field(default_factory=lambda: _env("TAGGER_MODEL", "gpt-5.6-terra"))
    synthesis_model: str = field(
        default_factory=lambda: _env("SYNTHESIS_MODEL", "gpt-5.6-sol")
    )
    tagger_reasoning_effort: ReasoningEffort = field(
        default_factory=lambda: _env_reasoning_effort("TAGGER_REASONING_EFFORT", "low")
    )
    synthesis_reasoning_effort: ReasoningEffort = field(
        default_factory=lambda: _env_reasoning_effort(
            "SYNTHESIS_REASONING_EFFORT", "medium"
        )
    )
    image_generation_mode: str = field(
        default_factory=lambda: _env("IMAGE_GENERATION_MODE", "fixture")
    )
    image_model: str = field(default_factory=lambda: _env("IMAGE_MODEL", "gpt-image-2"))
    asset_dir: Path = field(
        default_factory=lambda: Path(_env("REALCART_ASSET_DIR", "private-data/assets"))
    )
    api_public_base_url: str = field(
        default_factory=lambda: _env(
            "REALCART_API_PUBLIC_BASE_URL", "http://127.0.0.1:8000"
        ).rstrip("/")
    )
    web_public_base_url: str = field(
        default_factory=lambda: _env("REALCART_WEB_PUBLIC_BASE_URL", "http://localhost:3000")
    )
    google_client_id: str = field(default_factory=lambda: _env("GOOGLE_CLIENT_ID", ""))
    google_client_secret: str = field(
        default_factory=lambda: _env("GOOGLE_CLIENT_SECRET", "")
    )
    google_redirect_uri: str = field(
        default_factory=lambda: _env(
            "GOOGLE_REDIRECT_URI",
            "http://127.0.0.1:8000/api/auth/gmail/callback",
        )
    )
    gmail_access_token: str = field(
        default_factory=lambda: _env("GMAIL_ACCESS_TOKEN", "")
    )
    gmail_purchase_query: str = field(
        default_factory=lambda: _env(
            "GMAIL_PURCHASE_QUERY",
            "newer_than:1y "
            "(subject:(order OR receipt OR shipped OR delivered OR return OR refund))",
        )
    )
    gmail_max_messages: int = field(
        default_factory=lambda: int(_env("GMAIL_MAX_MESSAGES", "12"))
    )
    pinterest_client_id: str = field(
        default_factory=lambda: _env("PINTEREST_CLIENT_ID", "")
    )
    pinterest_client_secret: str = field(
        default_factory=lambda: _env("PINTEREST_CLIENT_SECRET", "")
    )
    pinterest_redirect_uri: str = field(
        default_factory=lambda: _env(
            "PINTEREST_REDIRECT_URI",
            "http://127.0.0.1:8000/api/auth/pinterest/callback",
        )
    )
    pinterest_access_token: str = field(
        default_factory=lambda: _env("PINTEREST_ACCESS_TOKEN", "")
    )
    pinterest_api_base_url: str = field(
        default_factory=lambda: _env(
            "PINTEREST_API_BASE_URL", "https://api-sandbox.pinterest.com/v5"
        ).rstrip("/")
    )
    pinterest_max_pins: int = field(
        default_factory=lambda: int(_env("PINTEREST_MAX_PINS", "16"))
    )
    openai_tracing_enabled: bool = field(
        default_factory=lambda: _env_bool("OPENAI_TRACING_ENABLED", True)
    )
    trace_include_sensitive_data: bool = field(
        default_factory=lambda: _env_bool("OPENAI_TRACE_INCLUDE_SENSITIVE_DATA", False)
    )


settings = Settings()
