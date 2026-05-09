from __future__ import annotations

from pathlib import Path

from dashboard.app import (
    build_overview_cards,
    metrics_for_display,
    select_default_run_id,
)

from microstructure_lab.execution.comparison import run_strategy_comparison
from microstructure_lab.execution.parent_order import ExecutionSide
from microstructure_lab.execution.simulator import run_execution_file
from microstructure_lab.runs.artifacts import leaderboard_rows, run_detail_payload, run_summaries
from microstructure_lab.simulation.synthetic import generate_events, write_events_csv


def test_dashboard_overview_helpers() -> None:
    runs = [
        {"run_id": "a", "status": "completed"},
        {"run_id": "b", "status": "failed"},
    ]

    cards = build_overview_cards(runs)

    assert cards == {"runs": 2, "completed": 1, "failed": 1}
    assert select_default_run_id(runs) == "b"
    assert select_default_run_id([]) is None


def test_artifact_helpers_read_indexed_runs(tmp_path: Path) -> None:
    output = tmp_path / "comparison"
    run_strategy_comparison(
        strategies=["twap", "pov"],
        scenario="normal",
        seed=42,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
        event_count=50,
    )

    runs = run_summaries()
    detail = run_detail_payload("comparison-normal-42-twap-pov")
    leaderboard = leaderboard_rows()

    assert any(run["run_id"] == "comparison-normal-42-twap-pov" for run in runs)
    assert detail is not None
    assert detail["manifest"]["run_id"] == "comparison-normal-42-twap-pov"
    assert any(row["source_run_id"] == "comparison-normal-42-twap-pov" for row in leaderboard)


def test_dashboard_metrics_for_execution_run(tmp_path: Path) -> None:
    events = generate_events(scenario="normal", seed=5, event_count=40)
    events_path = tmp_path / "events.csv"
    output = tmp_path / "twap"
    write_events_csv(events, events_path)
    run_execution_file(
        events_path=events_path,
        output_dir=output,
        strategy_name="twap",
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
    )

    metrics = metrics_for_display("execute-twap-buy-100-30")

    assert metrics["requested_quantity"] == 100
    assert "fill_rate" in metrics
