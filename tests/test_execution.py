from __future__ import annotations

import json
from pathlib import Path

from microstructure_lab.execution.adaptive import AdaptivePOVStrategy
from microstructure_lab.execution.base import ExecutionState
from microstructure_lab.execution.iceberg import IcebergStrategy
from microstructure_lab.execution.parent_order import ExecutionSide, ParentOrder
from microstructure_lab.execution.pov import POVStrategy
from microstructure_lab.execution.simulator import run_execution, run_execution_file
from microstructure_lab.execution.twap import TWAPStrategy
from microstructure_lab.execution.vwap import VWAPStrategy
from microstructure_lab.schemas.events import EventType, MarketEvent, OrderSide
from microstructure_lab.simulation.synthetic import generate_events, write_events_csv


def state(
    *,
    timestamp: int = 0,
    remaining_quantity: int = 1_000,
    spread_ticks: int = 4,
    observed_market_volume: int = 100,
) -> ExecutionState:
    return ExecutionState(
        timestamp=timestamp,
        elapsed_steps=timestamp,
        remaining_quantity=remaining_quantity,
        last_event=None,
        best_bid_ticks=10_000,
        best_ask_ticks=10_000 + spread_ticks,
        bid_depth=500,
        ask_depth=500,
        observed_market_volume=observed_market_volume,
    )


def parent(quantity: int = 1_000) -> ParentOrder:
    return ParentOrder(
        side=ExecutionSide.BUY,
        symbol="XYZ",
        quantity=quantity,
        start_time=0,
        end_time=10,
        participation_limit=0.1,
    )


def test_twap_slices_quantity() -> None:
    strategy = TWAPStrategy(slices=5)

    child = strategy.generate_child_orders(parent(1_000), state(timestamp=0))[0]

    assert child.quantity == 200
    assert child.strategy == "twap"


def test_pov_respects_participation_cap() -> None:
    strategy = POVStrategy(participation_rate=0.5)

    child = strategy.generate_child_orders(
        parent(1_000), state(timestamp=1, observed_market_volume=1_000)
    )[0]

    assert child.quantity == 100


def test_iceberg_reveals_child_size_progressively() -> None:
    strategy = IcebergStrategy(display_quantity=75)

    first = strategy.generate_child_orders(parent(1_000), state(timestamp=1))[0]
    final = strategy.generate_child_orders(
        parent(1_000), state(timestamp=2, remaining_quantity=20)
    )[0]

    assert first.quantity == 75
    assert final.quantity == 20


def test_adaptive_strategy_reacts_to_spread() -> None:
    strategy = AdaptivePOVStrategy(
        base_participation_rate=0.1,
        max_participation_rate=0.25,
        wide_spread_threshold_ticks=8,
    )

    tight = strategy.generate_child_orders(
        parent(1_000), state(timestamp=1, spread_ticks=4, observed_market_volume=100)
    )[0]
    wide = strategy.generate_child_orders(
        parent(1_000), state(timestamp=2, spread_ticks=12, observed_market_volume=100)
    )[0]

    assert tight.quantity == 25
    assert wide.quantity == 10


def test_vwap_uses_expected_schedule() -> None:
    strategy = VWAPStrategy(expected_volume_by_timestamp={0: 100, 1: 300})

    child = strategy.generate_child_orders(parent(400), state(timestamp=1))[0]

    assert child.quantity == 300
    assert strategy.schedule_source == "expected_static_volume_schedule"


def test_execution_result_includes_fills_and_unfilled_quantity() -> None:
    events = [
        MarketEvent(
            timestamp=0,
            sequence=0,
            event_type=EventType.ADD,
            symbol="XYZ",
            order_id="ask-1",
            side=OrderSide.SELL,
            price_ticks=101,
            quantity=100,
            scenario="normal",
            seed=1,
        ),
        MarketEvent(
            timestamp=1,
            sequence=1,
            event_type=EventType.ADD,
            symbol="XYZ",
            order_id="ask-2",
            side=OrderSide.SELL,
            price_ticks=102,
            quantity=100,
            scenario="normal",
            seed=1,
        ),
    ]

    result = run_execution(
        events=events,
        parent_order=ParentOrder(
            side=ExecutionSide.BUY,
            symbol="XYZ",
            quantity=150,
            start_time=0,
            end_time=2,
        ),
        strategy=TWAPStrategy(slices=2),
    )

    assert result.child_orders
    assert result.fills
    assert result.realized_quantity == 150
    assert result.unfilled_quantity == 0
    assert result.average_fill_price_ticks is not None


def test_execution_file_writes_artifacts(tmp_path: Path) -> None:
    events = generate_events(scenario="normal", seed=42, event_count=40)
    events_path = tmp_path / "events.csv"
    output = tmp_path / "twap_run"
    write_events_csv(events, events_path)

    result = run_execution_file(
        events_path=events_path,
        output_dir=output,
        strategy_name="twap",
        side=ExecutionSide.BUY,
        quantity=100,
        duration=20,
    )

    assert result.requested_quantity == 100
    assert (output / "child_orders.csv").exists()
    assert (output / "fills.csv").exists()
    assert (output / "result.json").exists()
    with (output / "result.json").open() as file:
        payload = json.load(file)
    assert payload["strategy"] == "twap"
