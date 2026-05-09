"""Shared artifact readers for API and dashboard views."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from microstructure_lab.runs.manifest import IndexedRun, find_indexed_run, list_indexed_runs


def run_summaries() -> list[dict[str, Any]]:
    return [run_summary(record) for record in list_indexed_runs()]


def run_summary(record: IndexedRun) -> dict[str, Any]:
    manifest = record.manifest
    return {
        "run_id": manifest.run_id,
        "status": manifest.status,
        "created_at": manifest.created_at,
        "scenario": manifest.scenario,
        "seed": manifest.seed,
        "strategy": manifest.strategy,
        "run_dir": record.run_dir,
    }


def run_detail_payload(run_id: str) -> dict[str, Any] | None:
    record = find_indexed_run(run_id)
    if record is None:
        return None
    return {
        "run_dir": record.run_dir,
        "manifest": record.manifest.model_dump(mode="json"),
        "artifacts": available_artifacts(record),
    }


def available_artifacts(record: IndexedRun) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    for name, artifact_path in record.manifest.output_paths.items():
        if Path(artifact_path).exists():
            artifacts[name] = artifact_path
    run_dir = Path(record.run_dir)
    for name in ["manifest.json", "result.json", "summary.json", "comparison_report.md"]:
        candidate_path = run_dir / name
        if candidate_path.exists():
            artifacts[name] = str(candidate_path)
    return artifacts


def result_metrics_for_run(run_id: str) -> dict[str, Any] | None:
    record = find_indexed_run(run_id)
    if record is None:
        return None
    return load_result_metrics(record)


def load_result_metrics(record: IndexedRun) -> dict[str, Any] | None:
    result_path = Path(record.run_dir) / "result.json"
    if not result_path.exists():
        return None
    with result_path.open() as file:
        result = json.load(file)
    return {
        "strategy": result.get("strategy"),
        "requested_quantity": result.get("requested_quantity"),
        "realized_quantity": result.get("realized_quantity"),
        "unfilled_quantity": result.get("unfilled_quantity"),
        "fill_rate": result.get("fill_rate"),
        "average_fill_price_ticks": result.get("average_fill_price_ticks"),
    }


def leaderboard_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in list_indexed_runs():
        manifest = record.manifest
        leaderboard = manifest.metrics.get("leaderboard")
        if isinstance(leaderboard, list):
            for row in leaderboard:
                rows.append(
                    {
                        "source_run_id": manifest.run_id,
                        "scenario": manifest.scenario,
                        **row,
                    }
                )
        elif manifest.strategy:
            rows.append(
                {
                    "source_run_id": manifest.run_id,
                    "scenario": manifest.scenario,
                    "strategy": manifest.strategy,
                    **manifest.metrics,
                }
            )
    return rows
