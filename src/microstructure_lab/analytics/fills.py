"""Fill quality metrics."""

from __future__ import annotations

import json
from pathlib import Path

from microstructure_lab.execution.parent_order import ExecutionResult


def load_execution_result(run_dir: Path) -> ExecutionResult:
    path = run_dir / "result.json"
    if not path.exists():
        msg = f"missing execution result artifact: {path}"
        raise FileNotFoundError(msg)
    with path.open() as file:
        payload = json.load(file)
    return ExecutionResult.model_validate(payload)


def realized_quantity(result: ExecutionResult) -> int:
    return sum(fill.quantity for fill in result.fills)


def average_fill_price_ticks(result: ExecutionResult) -> float | None:
    quantity = realized_quantity(result)
    if quantity == 0:
        return None
    notional = sum(fill.price_ticks * fill.quantity for fill in result.fills)
    return notional / quantity


def fill_rate(result: ExecutionResult) -> float:
    return realized_quantity(result) / result.requested_quantity


def unfilled_quantity(result: ExecutionResult) -> int:
    return result.requested_quantity - realized_quantity(result)


def time_to_completion(result: ExecutionResult) -> int | None:
    if realized_quantity(result) < result.requested_quantity or not result.fills:
        return None
    return max(fill.timestamp for fill in result.fills) - result.parent_order.start_time


def participation_rate(result: ExecutionResult) -> float | None:
    child_quantity = sum(child.quantity for child in result.child_orders)
    if child_quantity == 0:
        return None
    return realized_quantity(result) / child_quantity
