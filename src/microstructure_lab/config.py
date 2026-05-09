"""Configuration helpers for Microstructure-Lab."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AppConfig(BaseModel):
    """Runtime paths for local development and demos."""

    model_config = ConfigDict(frozen=True)

    data_dir: str = "data"
    artifact_dir: str = "artifacts"
