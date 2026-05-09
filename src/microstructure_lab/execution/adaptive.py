"""Adaptive POV execution strategy."""

from __future__ import annotations

from .base import ExecutionState, ExecutionStrategy, child_order
from .parent_order import ChildOrder, ParentOrder


class AdaptivePOVStrategy(ExecutionStrategy):
    name = "adaptive"

    def __init__(
        self,
        base_participation_rate: float = 0.1,
        max_participation_rate: float = 0.25,
        wide_spread_threshold_ticks: int = 8,
    ) -> None:
        if not 0 < base_participation_rate <= max_participation_rate <= 1:
            msg = "participation rates must satisfy 0 < base <= max <= 1"
            raise ValueError(msg)
        self.base_participation_rate = base_participation_rate
        self.max_participation_rate = max_participation_rate
        self.wide_spread_threshold_ticks = wide_spread_threshold_ticks

    def generate_child_orders(self, parent: ParentOrder, state: ExecutionState) -> list[ChildOrder]:
        in_window = parent.start_time <= state.timestamp <= parent.end_time
        if state.remaining_quantity <= 0 or not in_window:
            return []
        if state.observed_market_volume <= 0:
            return []

        rate = self.base_participation_rate
        if (
            state.spread_ticks is not None
            and state.spread_ticks <= self.wide_spread_threshold_ticks
        ):
            rate = self.max_participation_rate

        quantity = max(1, int(state.observed_market_volume * rate))
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
