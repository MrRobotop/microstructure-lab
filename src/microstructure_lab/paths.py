"""Repository-relative path helpers."""

from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return the repository root inferred from the installed source layout."""
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    """Return the default data directory."""
    return project_root() / "data"


def artifacts_dir() -> Path:
    """Return the default artifact directory."""
    return project_root() / "artifacts"
