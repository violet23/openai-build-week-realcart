"""Environment-backed runtime settings."""

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    data_mode: str = getenv("DATA_MODE", "fixture")
    analysis_mode: str = getenv("ANALYSIS_MODE", "fixture")
    tagger_model: str = getenv("TAGGER_MODEL", "gpt-5.6-terra")
    synthesis_model: str = getenv("SYNTHESIS_MODEL", "gpt-5.6-sol")


settings = Settings()
