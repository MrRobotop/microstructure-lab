"""POV execution strategy."""

from __future__ import annotations

from .base import ExecutionState, ExecutionStrategy, child_order
from .parent_order import ChildOrder, ParentOrder


class POVStrategy(ExecutionStrategy):
    name = "pov"

    def __init__(self, participation_rate: float = 0.1) -> None:
        if not 0 < participation_rate <= 1:
            msg = "participation_rate must be in (0, 1]"
            raise ValueError(msg)
        self.participation_rate = participation_rate

    def generate_child_orders(self, parent: ParentOrder, state: ExecutionState) -> list[ChildOrder]:
        in_window = parent.start_time <= state.timestamp <= parent.end_time
        if state.remaining_quantity <= 0 or not in_window:
            return []
        if state.observed_market_volume <= 0:
            return []
        limit = parent.participation_limit or self.participation_rate
        quantity = max(1, int(state.observed_market_volume * min(limit, self.participation_rate)))
        quantity = min(quantity, state.remaining_quantity)
        return [
            child_order(
                strategy=self.name,
                parent=parent,
                timestamp=state.timestamp,
                sequence=0,
                quantity=quantity,
            )
        ]
