"""Run manifests and artifact index."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from microstructure_lab import __version__
from microstructure_lab.orderbook import core
from microstructure_lab.paths import artifacts_dir


class RunManifest(BaseModel):
    """Human-readable reproducibility record for one run."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    created_at: str
    command: str
    git_commit: str | None = None
    scenario: str | None = None
    seed: int | None = None
    strategy: str | None = None
    parent_order: dict[str, Any] | None = None
    engine_version: str
    config_hash: str
    input_hash: str | None = None
    output_paths: dict[str, str] = Field(default_factory=dict)
    status: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    error: str | None = None


class IndexedRun(BaseModel):
    """Run manifest plus the artifact directory registered in the run index."""

    model_config = ConfigDict(frozen=True)

    run_dir: str
    manifest: RunManifest


def create_manifest(
    *,
    run_id: str,
    command: str,
    status: str,
    config: dict[str, Any],
    input_path: Path | None = None,
    output_paths: dict[str, Path | str] | None = None,
    scenario: str | None = None,
    seed: int | None = None,
    strategy: str | None = None,
    parent_order: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
    error: str | None = None,
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        command=command,
        git_commit=_git_commit(),
        scenario=scenario,
        seed=seed,
        strategy=strategy,
        parent_order=parent_order,
        engine_version=(
            f"microstructure-lab {__version__}; "
            f"core {core.load_core().engine_model_version()}"
        ),
        config_hash=stable_hash(config),
        input_hash=(
            file_hash(input_path) if input_path is not None and input_path.exists() else None
        ),
        output_paths={key: str(value) for key, value in (output_paths or {}).items()},
        status=status,
        metrics=metrics or {},
        limitations=limitations or [],
        error=error,
    )


def save_manifest(
    manifest: RunManifest,
    run_dir: Path,
    index_path: Path | None = None,
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "manifest.json"
    path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2))
    update_run_index(manifest, run_dir, index_path=index_path)
    return path


def load_manifest(path_or_run_dir: Path) -> RunManifest:
    path = path_or_run_dir / "manifest.json" if path_or_run_dir.is_dir() else path_or_run_dir
    with path.open() as file:
        return RunManifest.model_validate(json.load(file))


def list_manifests(index_path: Path | None = None) -> list[RunManifest]:
    return [record.manifest for record in list_indexed_runs(index_path)]


def list_indexed_runs(index_path: Path | None = None) -> list[IndexedRun]:
    path = index_path or default_index_path()
    if not path.exists():
        return []
    with path.open() as file:
        payload = json.load(file)
    return [IndexedRun.model_validate(item) for item in payload.get("runs", [])]


def find_manifest(run_id: str, index_path: Path | None = None) -> RunManifest | None:
    record = find_indexed_run(run_id, index_path)
    return record.manifest if record is not None else None


def find_indexed_run(run_id: str, index_path: Path | None = None) -> IndexedRun | None:
    for record in list_indexed_runs(index_path):
        if record.manifest.run_id == run_id:
            return record
    return None


def update_run_index(
    manifest: RunManifest,
    run_dir: Path,
    index_path: Path | None = None,
) -> Path:
    path = index_path or default_index_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        with path.open() as file:
            payload = json.load(file)
    else:
        payload = {"runs": []}

    entry = {"run_dir": str(run_dir), "manifest": manifest.model_dump(mode="json")}
    payload["runs"] = [
        item for item in payload.get("runs", []) if item["manifest"]["run_id"] != manifest.run_id
    ]
    payload["runs"].append(entry)
    payload["runs"].sort(key=lambda item: item["manifest"]["created_at"])
    path.write_text(json.dumps(payload, indent=2))
    return path


def default_index_path() -> Path:
    if override := os.environ.get("MICROSTRUCTURE_LAB_RUN_INDEX"):
        return Path(override)
    return artifacts_dir() / "runs" / "index.json"


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_run_id(prefix: str, parts: list[str | int | None]) -> str:
    clean = [str(part).replace("/", "-") for part in parts if part is not None and str(part) != ""]
    return "-".join([prefix, *clean])


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()
