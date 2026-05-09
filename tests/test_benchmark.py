from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from microstructure_lab.benchmarking.engine import benchmark_engine
from microstructure_lab.cli import app


def test_engine_benchmark_returns_conservative_observation() -> None:
    result = benchmark_engine(
        event_count=40,
        scenario="normal",
        seed=42,
        warmup_events=5,
    )

    assert result.synthetic is True
    assert result.scenario == "normal"
    assert result.seed == 42
    assert result.requested_events == 40
    assert result.applied_events == 40
    assert result.elapsed_seconds >= 0.0
    assert result.events_per_second >= 0.0
    assert any("not compare across machines" in item for item in result.limitations)


def test_engine_benchmark_rejects_invalid_event_count() -> None:
    with pytest.raises(ValueError, match="event_count must be positive"):
        benchmark_engine(event_count=0, scenario="normal")


def test_cli_benchmark_engine_writes_json(tmp_path) -> None:
    runner = CliRunner()
    output = tmp_path / "benchmark.json"

    result = runner.invoke(
        app,
        [
            "benchmark",
            "engine",
            "--events",
            "40",
            "--scenario",
            "normal",
            "--seed",
            "42",
            "--warmup-events",
            "5",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "Synthetic benchmark observation" in result.output
    assert "not a portable claim" in result.output
    payload = json.loads(output.read_text())
    assert payload["synthetic"] is True
    assert payload["applied_events"] == 40
    assert payload["scenario"] == "normal"
