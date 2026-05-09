"""Deterministic end-to-end demo workflow."""

from __future__ import annotations

from pathlib import Path

from microstructure_lab.execution.comparison import run_strategy_comparison
from microstructure_lab.execution.parent_order import ExecutionSide
from microstructure_lab.paths import project_root
from microstructure_lab.simulation.replay import replay_file


def run_demo(
    output_dir: Path | None = None,
    *,
    event_count: int = 150,
    quantity: int = 1_000,
    duration: int = 60,
) -> Path:
    """Run the deterministic synthetic demo and return the report path."""
    root = project_root()
    demo_dir = output_dir or root / "artifacts" / "runs" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    summary = run_strategy_comparison(
        strategies=["twap", "pov"],
        scenario="normal",
        seed=42,
        output_dir=demo_dir,
        side=ExecutionSide.BUY,
        quantity=quantity,
        duration=duration,
        event_count=event_count,
        arrival_price_ticks=10_000,
        command="microstructure-lab demo",
    )

    events_path = Path(summary["events_path"])
    replay_file(
        events_path,
        demo_dir / "book_replay",
        command="microstructure-lab demo",
    )

    return demo_dir / "comparison_report.md"
