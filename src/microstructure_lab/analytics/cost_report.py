"""Transaction cost report generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from microstructure_lab.execution.parent_order import ExecutionResult
from microstructure_lab.runs.manifest import (
    create_manifest,
    load_manifest,
    make_run_id,
    save_manifest,
)

from .fills import (
    average_fill_price_ticks,
    fill_rate,
    load_execution_result,
    participation_rate,
    realized_quantity,
    time_to_completion,
    unfilled_quantity,
)
from .impact import adverse_selection_proxy_ticks, spread_cost_ticks
from .implementation_shortfall import (
    implementation_shortfall_bps,
    implementation_shortfall_ticks,
    opportunity_cost_ticks,
    realized_shortfall_notional_ticks,
)
from .slippage import vwap_slippage_ticks


@dataclass(frozen=True)
class CostMetrics:
    strategy: str
    arrival_price_ticks: int | None
    average_fill_price_ticks: float | None
    realized_quantity: int
    fill_rate: float
    unfilled_quantity: int
    implementation_shortfall_ticks: float | None
    implementation_shortfall_bps: float | None
    vwap_slippage_ticks: float | None
    spread_cost_ticks: float | None
    time_to_completion: int | None
    participation_rate: float | None
    opportunity_cost_ticks: int | None
    adverse_selection_proxy_ticks: float | None
    realized_shortfall_notional_ticks: float | None


def compute_cost_metrics(
    result: ExecutionResult,
    *,
    arrival_price_ticks: int | None = None,
    benchmark_vwap_ticks: float | None = None,
    spread_ticks: int | None = None,
    terminal_mid_ticks: int | None = None,
) -> CostMetrics:
    return CostMetrics(
        strategy=result.strategy,
        arrival_price_ticks=arrival_price_ticks,
        average_fill_price_ticks=average_fill_price_ticks(result),
        realized_quantity=realized_quantity(result),
        fill_rate=fill_rate(result),
        unfilled_quantity=unfilled_quantity(result),
        implementation_shortfall_ticks=implementation_shortfall_ticks(
            result, arrival_price_ticks
        ),
        implementation_shortfall_bps=implementation_shortfall_bps(result, arrival_price_ticks),
        vwap_slippage_ticks=vwap_slippage_ticks(result, benchmark_vwap_ticks),
        spread_cost_ticks=spread_cost_ticks(result, spread_ticks),
        time_to_completion=time_to_completion(result),
        participation_rate=participation_rate(result),
        opportunity_cost_ticks=opportunity_cost_ticks(result, arrival_price_ticks),
        adverse_selection_proxy_ticks=adverse_selection_proxy_ticks(result, terminal_mid_ticks),
        realized_shortfall_notional_ticks=realized_shortfall_notional_ticks(
            result, arrival_price_ticks
        ),
    )


def write_cost_report(
    *,
    run_dir: Path,
    output_path: Path,
    arrival_price_ticks: int | None = None,
    benchmark_vwap_ticks: float | None = None,
    spread_ticks: int | None = None,
    terminal_mid_ticks: int | None = None,
    command: str | None = None,
) -> CostMetrics:
    result = load_execution_result(run_dir)
    metrics = compute_cost_metrics(
        result,
        arrival_price_ticks=arrival_price_ticks,
        benchmark_vwap_ticks=benchmark_vwap_ticks,
        spread_ticks=spread_ticks,
        terminal_mid_ticks=terminal_mid_ticks,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(result, metrics))
    run_manifest = None
    try:
        run_manifest = load_manifest(run_dir)
    except FileNotFoundError:
        run_manifest = None
    manifest = create_manifest(
        run_id=make_run_id("analytics-report", [run_dir.name]),
        command=command
        or f"microstructure-lab analytics report --run {run_dir} --output {output_path}",
        status="completed",
        config={
            "run_dir": str(run_dir),
            "arrival_price_ticks": arrival_price_ticks,
            "benchmark_vwap_ticks": benchmark_vwap_ticks,
            "spread_ticks": spread_ticks,
            "terminal_mid_ticks": terminal_mid_ticks,
        },
        input_path=run_dir / "result.json",
        output_paths={"report": output_path},
        scenario=run_manifest.scenario if run_manifest else None,
        seed=run_manifest.seed if run_manifest else None,
        strategy=result.strategy,
        parent_order=result.parent_order.model_dump(mode="json"),
        metrics=metrics.__dict__,
        limitations=[
            "Synthetic transaction cost analytics.",
            "Missing benchmarks are reported as unavailable.",
        ],
    )
    save_manifest(manifest, output_path.parent)
    return metrics


def render_markdown_report(result: ExecutionResult, metrics: CostMetrics) -> str:
    lines = [
        "# Transaction Cost Report",
        "",
        "Data label: synthetic execution simulation.",
        "",
        "## Parent Order",
        "",
        f"- Strategy: `{result.strategy}`",
        f"- Side: `{result.parent_order.side}`",
        f"- Requested quantity: `{result.requested_quantity}`",
        f"- Child orders: `{len(result.child_orders)}`",
        f"- Fills: `{len(result.fills)}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value | Units |",
        "|---|---:|---|",
    ]
    rows = [
        ("Arrival price", metrics.arrival_price_ticks, "ticks"),
        ("Average fill price", metrics.average_fill_price_ticks, "ticks"),
        ("Realized quantity", metrics.realized_quantity, "quantity"),
        ("Fill rate", metrics.fill_rate, "ratio"),
        ("Unfilled quantity", metrics.unfilled_quantity, "quantity"),
        ("Implementation shortfall", metrics.implementation_shortfall_ticks, "ticks/share"),
        ("Implementation shortfall", metrics.implementation_shortfall_bps, "bps"),
        ("VWAP slippage", metrics.vwap_slippage_ticks, "ticks/share"),
        ("Spread cost estimate", metrics.spread_cost_ticks, "tick-notional"),
        ("Time to completion", metrics.time_to_completion, "event-time"),
        ("Participation rate", metrics.participation_rate, "ratio"),
        ("Opportunity cost", metrics.opportunity_cost_ticks, "tick-notional"),
        (
            "Adverse selection proxy",
            metrics.adverse_selection_proxy_ticks,
            "ticks/share",
        ),
        (
            "Realized shortfall notional",
            metrics.realized_shortfall_notional_ticks,
            "tick-notional",
        ),
    ]
    for label, value, units in rows:
        lines.append(f"| {label} | {_format_value(value)} | {units} |")

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Synthetic results are for deterministic engineering demos only.",
            "- Missing benchmarks are reported as unavailable, not estimated.",
            "- Phase 7 analytics do not calibrate market impact from real data.",
            "- Partial fills and unfilled quantity are included explicitly.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_value(value: float | int | None) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)
