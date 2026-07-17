"""Environment-backed runtime settings."""

from dataclasses import dataclass, field
from os import getenv
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
    openai_tracing_enabled: bool = field(
        default_factory=lambda: _env_bool("OPENAI_TRACING_ENABLED", True)
    )
    trace_include_sensitive_data: bool = field(
        default_factory=lambda: _env_bool("OPENAI_TRACE_INCLUDE_SENSITIVE_DATA", False)
    )


settings = Settings()
