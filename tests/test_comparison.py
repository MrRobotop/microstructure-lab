from __future__ import annotations

import json
from pathlib import Path

from microstructure_lab.analytics.leaderboard import LeaderboardRow, rank_strategies
from microstructure_lab.execution.comparison import run_strategy_comparison
from microstructure_lab.execution.parent_order import ExecutionSide


def test_all_strategies_run_on_same_synthetic_event_stream(tmp_path: Path) -> None:
    output = tmp_path / "comparison"

    summary = run_strategy_comparison(
        strategies=["twap", "pov"],
        scenario="normal",
        seed=42,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=40,
        event_count=60,
    )

    assert summary["synthetic"] is True
    assert summary["events_path"] == str(output / "events.csv")
    assert (output / "events.csv").exists()
    assert (output / "twap" / "result.json").exists()
    assert (output / "pov" / "result.json").exists()


def test_comparison_writes_summary_and_report(tmp_path: Path) -> None:
    output = tmp_path / "comparison"

    run_strategy_comparison(
        strategies=["twap", "vwap", "pov"],
        scenario="normal",
        seed=7,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
        event_count=60,
        arrival_price_ticks=10_000,
    )

    summary_path = output / "summary.json"
    report_path = output / "comparison_report.md"
    assert summary_path.exists()
    assert report_path.exists()

    summary = json.loads(summary_path.read_text())
    report = report_path.read_text()
    assert summary["synthetic"] is True
    assert "Strategy Comparison Report" in report
    assert "Data label: synthetic execution simulation." in report
    assert "Ranking uses fill rate" in report


def test_leaderboard_handles_missing_metrics() -> None:
    rows = [
        LeaderboardRow(
            strategy="missing",
            fill_rate=1.0,
            average_fill_price_ticks=101,
            implementation_shortfall_bps=None,
            unfilled_quantity=0,
        ),
        LeaderboardRow(
            strategy="available",
            fill_rate=1.0,
            average_fill_price_ticks=101,
            implementation_shortfall_bps=5,
            unfilled_quantity=0,
        ),
    ]

    ranked = rank_strategies(rows)

    assert ranked[0].strategy == "available"


def test_ranking_uses_multiple_metrics_not_one_metric_only() -> None:
    rows = [
        LeaderboardRow(
            strategy="low_fill_low_shortfall",
            fill_rate=0.5,
            average_fill_price_ticks=100,
            implementation_shortfall_bps=0,
            unfilled_quantity=50,
        ),
        LeaderboardRow(
            strategy="high_fill_higher_shortfall",
            fill_rate=0.9,
            average_fill_price_ticks=105,
            implementation_shortfall_bps=50,
            unfilled_quantity=10,
        ),
    ]

    ranked = rank_strategies(rows)

    assert ranked[0].strategy == "high_fill_higher_shortfall"


def test_report_clearly_labels_synthetic_data(tmp_path: Path) -> None:
    output = tmp_path / "comparison"

    run_strategy_comparison(
        strategies=["twap", "iceberg", "adaptive"],
        scenario="thin_liquidity",
        seed=9,
        output_dir=output,
        side=ExecutionSide.SELL,
        quantity=100,
        duration=40,
        event_count=70,
    )

    report = (output / "comparison_report.md").read_text()
    assert "synthetic execution simulation" in report
    assert "Rankings do not prove live trading quality" in report
