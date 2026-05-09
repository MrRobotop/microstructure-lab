"""Simple impact and spread cost proxies."""

from __future__ import annotations

from microstructure_lab.execution.parent_order import ExecutionResult, ExecutionSide

from .fills import realized_quantity


def spread_cost_ticks(result: ExecutionResult, spread_ticks: int | None) -> float | None:
    if spread_ticks is None:
        return None
    return spread_ticks / 2 * realized_quantity(result)


def adverse_selection_proxy_ticks(
    result: ExecutionResult,
    terminal_mid_ticks: int | None,
) -> float | None:
    if terminal_mid_ticks is None or not result.fills:
        return None
    last_fill = result.fills[-1]
    if result.parent_order.side == ExecutionSide.BUY:
        return terminal_mid_ticks - last_fill.price_ticks
    return last_fill.price_ticks - terminal_mid_ticks
