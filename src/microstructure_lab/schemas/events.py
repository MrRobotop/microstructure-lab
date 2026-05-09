"""Schemas for synthetic order book events."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventType(StrEnum):
    ADD = "add"
    CANCEL = "cancel"
    MODIFY = "modify"
    MARKET = "market"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class MarketEvent(BaseModel):
    """Validated event row used by synthetic generation and replay."""

    model_config = ConfigDict(frozen=True)

    timestamp: int = Field(ge=0)
    sequence: int = Field(ge=0)
    event_type: EventType
    symbol: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    side: OrderSide | None = None
    price_ticks: int | None = None
    quantity: int | None = None
    scenario: str = Field(min_length=1)
    seed: int
    is_synthetic: bool = True

    @model_validator(mode="after")
    def validate_event_fields(self) -> MarketEvent:
        if not self.is_synthetic:
            msg = "Phase 5 replay only accepts explicitly synthetic events"
            raise ValueError(msg)
        if self.event_type in {EventType.ADD, EventType.MARKET} and self.side is None:
            msg = f"{self.event_type} events require side"
            raise ValueError(msg)
        if self.event_type in {EventType.ADD, EventType.MODIFY} and (
            self.price_ticks is None or self.price_ticks <= 0
        ):
            msg = f"{self.event_type} events require positive price_ticks"
            raise ValueError(msg)
        if self.event_type in {EventType.ADD, EventType.MODIFY, EventType.MARKET} and (
            self.quantity is None or self.quantity <= 0
        ):
            msg = f"{self.event_type} events require positive quantity"
            raise ValueError(msg)
        if self.event_type == EventType.CANCEL and (
            self.side is not None or self.price_ticks is not None or self.quantity is not None
        ):
            msg = "cancel events must not include side, price_ticks, or quantity"
            raise ValueError(msg)
        if self.event_type == EventType.MARKET and self.price_ticks is not None:
            msg = "market events must not include price_ticks"
            raise ValueError(msg)
        return self


EVENT_COLUMNS = [
    "timestamp",
    "sequence",
    "event_type",
    "symbol",
    "order_id",
    "side",
    "price_ticks",
    "quantity",
    "scenario",
    "seed",
    "is_synthetic",
]
