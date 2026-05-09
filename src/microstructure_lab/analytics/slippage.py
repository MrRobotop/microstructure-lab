"""Slippage metrics."""

from __future__ import annotations

from microstructure_lab.execution.parent_order import ExecutionResult, ExecutionSide

from .fills import average_fill_price_ticks


def arrival_slippage_ticks(
    result: ExecutionResult,
    arrival_price_ticks: int | None,
) -> float | None:
    avg_fill = average_fill_price_ticks(result)
    if arrival_price_ticks is None or avg_fill is None:
        return None
    if result.parent_order.side == ExecutionSide.BUY:
        return avg_fill - arrival_price_ticks
    return arrival_price_ticks - avg_fill


def vwap_slippage_ticks(
    result: ExecutionResult,
    benchmark_vwap_ticks: float | None,
) -> float | None:
    avg_fill = average_fill_price_ticks(result)
    if benchmark_vwap_ticks is None or avg_fill is None:
        return None
    if result.parent_order.side == ExecutionSide.BUY:
        return avg_fill - benchmark_vwap_ticks
    return benchmark_vwap_ticks - avg_fill
