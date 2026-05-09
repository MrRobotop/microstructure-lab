"""Implementation shortfall metrics."""

from __future__ import annotations

from microstructure_lab.execution.parent_order import ExecutionResult, ExecutionSide

from .fills import average_fill_price_ticks, realized_quantity, unfilled_quantity


def implementation_shortfall_ticks(
    result: ExecutionResult,
    arrival_price_ticks: int | None,
) -> float | None:
    avg_fill = average_fill_price_ticks(result)
    if arrival_price_ticks is None or avg_fill is None:
        return None
    if result.parent_order.side == ExecutionSide.BUY:
        return avg_fill - arrival_price_ticks
    return arrival_price_ticks - avg_fill


def implementation_shortfall_bps(
    result: ExecutionResult,
    arrival_price_ticks: int | None,
) -> float | None:
    shortfall = implementation_shortfall_ticks(result, arrival_price_ticks)
    if shortfall is None or arrival_price_ticks is None or arrival_price_ticks <= 0:
        return None
    return shortfall / arrival_price_ticks * 10_000


def opportunity_cost_ticks(
    result: ExecutionResult,
    arrival_price_ticks: int | None,
) -> int | None:
    if arrival_price_ticks is None:
        return None
    return unfilled_quantity(result) * arrival_price_ticks


def realized_shortfall_notional_ticks(
    result: ExecutionResult,
    arrival_price_ticks: int | None,
) -> float | None:
    shortfall = implementation_shortfall_ticks(result, arrival_price_ticks)
    if shortfall is None:
        return None
    return shortfall * realized_quantity(result)
