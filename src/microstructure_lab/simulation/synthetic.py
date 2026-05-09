"""Deterministic synthetic order flow generation."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from microstructure_lab.schemas.events import EVENT_COLUMNS, EventType, MarketEvent, OrderSide
from microstructure_lab.simulation.scenarios import get_scenario


def generate_events(
    *,
    scenario: str,
    seed: int,
    event_count: int = 100,
    symbol: str = "XYZ",
) -> list[MarketEvent]:
    """Generate deterministic synthetic events for one symbol."""
    if event_count <= 0:
        msg = "event_count must be positive"
        raise ValueError(msg)

    config = get_scenario(scenario)
    rng = random.Random(seed)
    events: list[MarketEvent] = []
    active_orders: list[str] = []
    sequence = 0

    def append(
        *,
        event_type: EventType,
        order_id: str,
        side: OrderSide | None = None,
        price_ticks: int | None = None,
        quantity: int | None = None,
    ) -> None:
        nonlocal sequence
        events.append(
            MarketEvent(
                timestamp=sequence,
                sequence=sequence,
                event_type=event_type,
                symbol=symbol,
                order_id=order_id,
                side=side,
                price_ticks=price_ticks,
                quantity=quantity,
                scenario=scenario,
                seed=seed,
                is_synthetic=True,
            )
        )
        sequence += 1

    half_spread = max(1, config.spread_ticks // 2)
    for level in range(config.initial_depth):
        bid_price = config.base_mid_ticks - half_spread - level
        ask_price = config.base_mid_ticks + half_spread + level
        bid_id = f"seed-bid-{level}"
        ask_id = f"seed-ask-{level}"
        quantity = config.quantity_max
        append(
            event_type=EventType.ADD,
            order_id=bid_id,
            side=OrderSide.BUY,
            price_ticks=bid_price,
            quantity=quantity,
        )
        active_orders.append(bid_id)
        append(
            event_type=EventType.ADD,
            order_id=ask_id,
            side=OrderSide.SELL,
            price_ticks=ask_price,
            quantity=quantity,
        )
        active_orders.append(ask_id)

    while len(events) < event_count:
        idx = len(events)
        quantity = rng.randint(config.quantity_min, config.quantity_max)

        if idx % config.market_order_frequency == 0:
            side = rng.choice([OrderSide.BUY, OrderSide.SELL])
            append(
                event_type=EventType.MARKET,
                order_id=f"mkt-{idx}",
                side=side,
                quantity=quantity,
            )
            continue

        if active_orders and idx % config.cancel_frequency == 0:
            order_id = active_orders.pop(rng.randrange(len(active_orders)))
            append(event_type=EventType.CANCEL, order_id=order_id)
            continue

        side = rng.choice([OrderSide.BUY, OrderSide.SELL])
        jitter = rng.randint(0, config.price_jitter_ticks)
        if side == OrderSide.BUY:
            price_ticks = config.base_mid_ticks - half_spread - jitter
        else:
            price_ticks = config.base_mid_ticks + half_spread + jitter
        order_id = f"lim-{idx}"
        append(
            event_type=EventType.ADD,
            order_id=order_id,
            side=side,
            price_ticks=price_ticks,
            quantity=quantity,
        )
        active_orders.append(order_id)

    return events[:event_count]


def write_events_csv(events: list[MarketEvent], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=EVENT_COLUMNS)
        writer.writeheader()
        for event in events:
            row = event.model_dump(mode="json")
            writer.writerow({column: row.get(column) for column in EVENT_COLUMNS})


def read_events_csv(path: Path) -> list[MarketEvent]:
    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        missing = set(EVENT_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            msg = f"event file missing required columns: {sorted(missing)}"
            raise ValueError(msg)
        return [_event_from_csv_row(row) for row in reader]


def _event_from_csv_row(row: dict[str, str]) -> MarketEvent:
    def optional_int(value: str) -> int | None:
        return None if value == "" else int(value)

    def optional_side(value: str) -> OrderSide | None:
        return None if value == "" else OrderSide(value)

    return MarketEvent(
        timestamp=int(row["timestamp"]),
        sequence=int(row["sequence"]),
        event_type=EventType(row["event_type"]),
        symbol=row["symbol"],
        order_id=row["order_id"],
        side=optional_side(row["side"]),
        price_ticks=optional_int(row["price_ticks"]),
        quantity=optional_int(row["quantity"]),
        scenario=row["scenario"],
        seed=int(row["seed"]),
        is_synthetic=row["is_synthetic"].lower() == "true",
    )
