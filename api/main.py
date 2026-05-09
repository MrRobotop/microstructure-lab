"""FastAPI service for reading stored Microstructure-Lab artifacts."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from microstructure_lab.runs.artifacts import (
    leaderboard_rows,
    result_metrics_for_run,
    run_detail_payload,
    run_summaries,
)
from microstructure_lab.runs.manifest import IndexedRun, find_indexed_run

app = FastAPI(
    title="Microstructure-Lab API",
    version="0.1.0",
    description="Read-only API for synthetic run artifacts.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/runs")
def runs() -> list[dict[str, Any]]:
    return run_summaries()


@app.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    payload = run_detail_payload(run_id)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
    return payload


@app.get("/runs/{run_id}/metrics")
def run_metrics(run_id: str) -> dict[str, Any]:
    record = _get_record(run_id)
    return {
        "run_id": record.manifest.run_id,
        "manifest_metrics": record.manifest.metrics,
        "result_metrics": result_metrics_for_run(run_id),
    }


@app.get("/leaderboard")
def leaderboard() -> list[dict[str, Any]]:
    return leaderboard_rows()


def _get_record(run_id: str) -> IndexedRun:
    record = find_indexed_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"run_id not found: {run_id}")
    return record
