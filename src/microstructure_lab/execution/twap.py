"""TWAP execution strategy."""

from __future__ import annotations

from .base import ExecutionState, ExecutionStrategy, child_order
from .parent_order import ChildOrder, ParentOrder


class TWAPStrategy(ExecutionStrategy):
    name = "twap"

    def __init__(self, slices: int = 10) -> None:
        if slices <= 0:
            msg = "slices must be positive"
            raise ValueError(msg)
        self.slices = slices

    def generate_child_orders(self, parent: ParentOrder, state: ExecutionState) -> list[ChildOrder]:
        if state.remaining_quantity <= 0 or state.timestamp < parent.start_time:
            return []
        if state.timestamp >= parent.end_time:
            return [
                child_order(
                    strategy=self.name,
                    parent=parent,
                    timestamp=state.timestamp,
                    sequence=0,
                    quantity=state.remaining_quantity,
                )
            ]

        interval = max(1, (parent.end_time - parent.start_time) // self.slices)
        if (state.timestamp - parent.start_time) % interval != 0:
            return []
        slice_quantity = max(1, parent.quantity // self.slices)
        quantity = min(slice_quantity, state.remaining_quantity)
        return [
            child_order(
                strategy=self.name,
                parent=parent,
                timestamp=state.timestamp,
                sequence=0,
                quantity=quantity,
            )
        ]
