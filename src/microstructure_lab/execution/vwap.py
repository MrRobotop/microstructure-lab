"""VWAP execution strategy using an expected static volume schedule."""

from __future__ import annotations

from .base import ExecutionState, ExecutionStrategy, child_order
from .parent_order import ChildOrder, ParentOrder


class VWAPStrategy(ExecutionStrategy):
    name = "vwap"

    def __init__(self, expected_volume_by_timestamp: dict[int, int] | None = None) -> None:
        self.expected_volume_by_timestamp = expected_volume_by_timestamp or {}
        self.schedule_source = "expected_static_volume_schedule"

    def generate_child_orders(self, parent: ParentOrder, state: ExecutionState) -> list[ChildOrder]:
        in_window = parent.start_time <= state.timestamp <= parent.end_time
        if state.remaining_quantity <= 0 or not in_window:
            return []

        expected_volume = self.expected_volume_by_timestamp.get(state.timestamp, 0)
        total_expected = sum(self.expected_volume_by_timestamp.values())
        if expected_volume <= 0 or total_expected <= 0:
            return []

        target = max(1, round(parent.quantity * expected_volume / total_expected))
        quantity = min(target, state.remaining_quantity)
        return [
            child_order(
                strategy=self.name,
                parent=parent,
                timestamp=state.timestamp,
                sequence=0,
                quantity=quantity,
            )
        ]
