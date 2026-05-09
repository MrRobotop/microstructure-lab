"""Execution strategy interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from microstructure_lab.schemas.events import MarketEvent

from .parent_order import ChildOrder, ParentOrder


@dataclass(frozen=True)
class ExecutionState:
    """State visible to a strategy at a replay timestamp."""

    timestamp: int
    elapsed_steps: int
    remaining_quantity: int
    last_event: MarketEvent | None
    best_bid_ticks: int | None
    best_ask_ticks: int | None
    bid_depth: int
    ask_depth: int
    observed_market_volume: int

    @property
    def spread_ticks(self) -> int | None:
        if self.best_bid_ticks is None or self.best_ask_ticks is None:
            return None
        return self.best_ask_ticks - self.best_bid_ticks


class ExecutionStrategy(ABC):
    """Base interface for execution strategies."""

    name: str

    @abstractmethod
    def generate_child_orders(self, parent: ParentOrder, state: ExecutionState) -> list[ChildOrder]:
        """Return child orders for the current replay state."""


def child_order(
    *,
    strategy: str,
    parent: ParentOrder,
    timestamp: int,
    sequence: int,
    quantity: int,
) -> ChildOrder:
    return ChildOrder(
        child_order_id=f"{strategy}-{timestamp}-{sequence}",
        timestamp=timestamp,
        symbol=parent.symbol,
        side=parent.side,
        quantity=min(quantity, parent.quantity),
        strategy=strategy,
    )
