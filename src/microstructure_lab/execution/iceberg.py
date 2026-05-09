"""Iceberg execution strategy."""

from __future__ import annotations

from .base import ExecutionState, ExecutionStrategy, child_order
from .parent_order import ChildOrder, ParentOrder


class IcebergStrategy(ExecutionStrategy):
    name = "iceberg"

    def __init__(self, display_quantity: int = 100) -> None:
        if display_quantity <= 0:
            msg = "display_quantity must be positive"
            raise ValueError(msg)
        self.display_quantity = display_quantity

    def generate_child_orders(self, parent: ParentOrder, state: ExecutionState) -> list[ChildOrder]:
        in_window = parent.start_time <= state.timestamp <= parent.end_time
        if state.remaining_quantity <= 0 or not in_window:
            return []
        quantity = min(self.display_quantity, state.remaining_quantity)
        return [
            child_order(
                strategy=self.name,
                parent=parent,
                timestamp=state.timestamp,
                sequence=0,
                quantity=quantity,
            )
        ]
