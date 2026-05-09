"""Strategy comparison runner."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from microstructure_lab.analytics.cost_report import CostMetrics, compute_cost_metrics
from microstructure_lab.analytics.leaderboard import LeaderboardRow, rank_strategies
from microstructure_lab.execution.parent_order import ExecutionResult, ExecutionSide, ParentOrder
from microstructure_lab.execution.simulator import (
    run_execution,
    strategy_from_name,
    write_execution_artifacts,
)
from microstructure_lab.runs.manifest import create_manifest, make_run_id, save_manifest
from microstructure_lab.simulation.synthetic import generate_events, write_events_csv


def run_strategy_comparison(
    *,
    strategies: list[str],
    scenario: str,
    seed: int,
    output_dir: Path,
    side: ExecutionSide = ExecutionSide.BUY,
    quantity: int = 10_000,
    duration: int = 60,
    event_count: int = 200,
    arrival_price_ticks: int | None = None,
    benchmark_vwap_ticks: float | None = None,
    spread_ticks: int | None = None,
    terminal_mid_ticks: int | None = None,
    command: str | None = None,
) -> dict:
    if not strategies:
        msg = "at least one strategy is required"
        raise ValueError(msg)

    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = make_run_id("comparison", [scenario, seed, "-".join(strategies)])
    config = {
        "strategies": strategies,
        "scenario": scenario,
        "seed": seed,
        "side": side.value,
        "quantity": quantity,
        "duration": duration,
        "event_count": event_count,
        "arrival_price_ticks": arrival_price_ticks,
        "benchmark_vwap_ticks": benchmark_vwap_ticks,
        "spread_ticks": spread_ticks,
        "terminal_mid_ticks": terminal_mid_ticks,
    }
    try:
        events = generate_events(scenario=scenario, seed=seed, event_count=event_count)
        events_path = output_dir / "events.csv"
        write_events_csv(events, events_path)

        parent_order = ParentOrder(
            side=side,
            quantity=quantity,
            start_time=0,
            end_time=duration,
        )
        results: list[ExecutionResult] = []
        metrics_rows: list[CostMetrics] = []
        leaderboard_rows: list[LeaderboardRow] = []

        for strategy_name in strategies:
            strategy = strategy_from_name(strategy_name, events)
            result = run_execution(events=events, parent_order=parent_order, strategy=strategy)
            strategy_dir = output_dir / strategy.name
            write_execution_artifacts(result, strategy_dir)
            metrics = compute_cost_metrics(
                result,
                arrival_price_ticks=arrival_price_ticks,
                benchmark_vwap_ticks=benchmark_vwap_ticks,
                spread_ticks=spread_ticks,
                terminal_mid_ticks=terminal_mid_ticks,
            )
            results.append(result)
            metrics_rows.append(metrics)
            leaderboard_rows.append(
                LeaderboardRow(
                    strategy=result.strategy,
                    fill_rate=metrics.fill_rate,
                    average_fill_price_ticks=metrics.average_fill_price_ticks,
                    implementation_shortfall_bps=metrics.implementation_shortfall_bps,
                    unfilled_quantity=metrics.unfilled_quantity,
                )
            )

        ranked = rank_strategies(leaderboard_rows)
        summary = _summary_payload(
            scenario=scenario,
            seed=seed,
            event_count=event_count,
            events_path=events_path,
            parent_order=parent_order,
            results=results,
            metrics_rows=metrics_rows,
            ranked=ranked,
        )
        summary_path = output_dir / "summary.json"
        report_path = output_dir / "comparison_report.md"
        summary_path.write_text(json.dumps(summary, indent=2))
        report_path.write_text(render_comparison_report(summary, metrics_rows, ranked))
        manifest = create_manifest(
            run_id=run_id,
            command=command or _comparison_command(config, output_dir),
            status="completed",
            config=config,
            input_path=events_path,
            output_paths={
                "events": events_path,
                "summary": summary_path,
                "report": report_path,
            },
            scenario=scenario,
            seed=seed,
            strategy=",".join(summary["strategies"]),
            parent_order=parent_order.model_dump(mode="json"),
            metrics={"leaderboard": summary["leaderboard"]},
            limitations=[
                "Synthetic data is shared across strategies.",
                "Rankings do not prove live trading quality.",
            ],
        )
        save_manifest(manifest, output_dir)
        return summary
    except Exception as exc:
        manifest = create_manifest(
            run_id=run_id,
            command=command or _comparison_command(config, output_dir),
            status="failed",
            config=config,
            output_paths={},
            scenario=scenario,
            seed=seed,
            strategy=",".join(strategies),
            error=str(exc),
            limitations=["Failed comparison recorded for auditability."],
        )
        save_manifest(manifest, output_dir)
        raise


def render_comparison_report(
    summary: dict,
    metrics_rows: list[CostMetrics],
    ranked: list[LeaderboardRow],
) -> str:
    lines = [
        "# Strategy Comparison Report",
        "",
        "Data label: synthetic execution simulation.",
        "",
        "## Scenario",
        "",
        f"- Scenario: `{summary['scenario']}`",
        f"- Seed: `{summary['seed']}`",
        f"- Event count: `{summary['event_count']}`",
        "",
        "## Leaderboard",
        "",
        "Ranking uses fill rate, implementation shortfall when available, and unfilled quantity.",
        "",
        "| Rank | Strategy | Fill rate | IS bps | Unfilled quantity |",
        "|---:|---|---:|---:|---:|",
    ]
    for index, row in enumerate(ranked, start=1):
        is_bps = _format_value(row.implementation_shortfall_bps)
        lines.append(
            f"| {index} | {row.strategy} | {row.fill_rate:.6g} | "
            f"{is_bps} | {row.unfilled_quantity} |"
        )

    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| Strategy | Avg fill ticks | Realized | Fill rate | Unfilled | VWAP slip |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for metrics in metrics_rows:
        avg = _format_value(metrics.average_fill_price_ticks)
        vwap = _format_value(metrics.vwap_slippage_ticks)
        lines.append(
            f"| {metrics.strategy} | {avg} | {metrics.realized_quantity} | "
            f"{metrics.fill_rate:.6g} | {metrics.unfilled_quantity} | {vwap} |"
        )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Synthetic data is shared across strategies for a deterministic comparison.",
            "- Rankings do not prove live trading quality.",
            "- Missing benchmark-dependent metrics are shown as unavailable.",
            "- Strategies use the same synthetic event stream and C++ matching engine.",
            "",
        ]
    )
    return "\n".join(lines)


def _summary_payload(
    *,
    scenario: str,
    seed: int,
    event_count: int,
    events_path: Path,
    parent_order: ParentOrder,
    results: list[ExecutionResult],
    metrics_rows: list[CostMetrics],
    ranked: list[LeaderboardRow],
) -> dict:
    return {
        "synthetic": True,
        "scenario": scenario,
        "seed": seed,
        "event_count": event_count,
        "events_path": str(events_path),
        "parent_order": parent_order.model_dump(mode="json"),
        "strategies": [result.strategy for result in results],
        "metrics": [asdict(metrics) for metrics in metrics_rows],
        "leaderboard": [asdict(row) for row in ranked],
    }


def _format_value(value: float | int | None) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _comparison_command(config: dict[str, object], output_dir: Path) -> str:
    strategies = config["strategies"]
    if not isinstance(strategies, list):
        msg = "comparison command config requires a list of strategies"
        raise TypeError(msg)
    return (
        "microstructure-lab execute compare "
        f"--strategies {','.join(str(item) for item in strategies)} "
        f"--scenario {config['scenario']} "
        f"--seed {config['seed']} "
        f"--side {config['side']} "
        f"--quantity {config['quantity']} "
        f"--duration {config['duration']} "
        f"--events {config['event_count']} "
        f"--output {output_dir}"
    )
